import asyncio
import copy
import logging
import time
from datetime import datetime

from src.main.clients import SeleniumClient
from src.main.dao import UserDAO, FilterDAO
from src.main.handlers.keyboards import shift_mute_keyboard
from src.main.schemas import ShiftBase, FilterBase
from src.main.services.message_service import MessageService
from src.main.services.mute_service import MuteService
from src.main.exceptions.selenium_exceptions import (
    SeleniumCommandException,
    SeleniumCommandTimeoutException,
    SeleniumWebDriverNotReadyException
)


class ShiftService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ShiftService, cls).__new__(cls)
        return cls._instance

    def __init__(self,
                 user_dao: UserDAO,
                 filter_dao: FilterDAO,
                 selenium_client: SeleniumClient):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._search_timeout = 10
            self._login_timeout = 30
            self._mute_clean_timeout = 60
            self._driver = None
            self._login_task = None
            self._search_task = None
            self._mute_cleanup_task = None
            self._user_dao = user_dao
            self._filter_dao = filter_dao
            self._selenium_client = selenium_client
            self._existing_shift_links: set[int] = set()        
            self._driver_mutex = asyncio.Lock()
    
    @classmethod
    def initialize(cls, user_dao: UserDAO, filter_dao: FilterDAO, selenium_client: SeleniumClient):
        if cls._instance:
            raise RuntimeError("ShiftService is already initialized. Use get_instance() to access it.")
        cls._instance = cls(user_dao, filter_dao, selenium_client)
    
    @classmethod
    def get_instance(cls) -> 'ShiftService':
        if not cls._instance:
            raise RuntimeError("ShiftService is not initialized. Call initialize() first.")
        return cls._instance

    @staticmethod
    async def _notify_admins_critical_error(error_type: str, error_message: str, exception: Exception = None) -> None:
        try:
            message_service = MessageService.get_instance()
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            admin_message = f"🚨 <b>КРИТИЧЕСКАЯ ОШИБКА ShiftService</b>\n\n"
            admin_message += f"⏰ Время: {timestamp}\n"
            admin_message += f"🔴 Тип ошибки: {error_type}\n"
            admin_message += f"📝 Сообщение: {error_message}\n"
            
            if exception:
                admin_message += f"🔍 Детали: {str(exception)}\n"
            
            admin_message += f"\n⚠️ Требуется вмешательство администратора!"
            
            await message_service.send_message_all_admin(admin_message, protect_content=False)
            logging.critical(f"Critical error in ShiftService: {error_type} - {error_message}", exc_info=exception)
            
        except Exception as e:
            logging.error(f"Failed to notify admins about critical error: {e}")

    @staticmethod
    async def _handle_selenium_error(error_type: str, exception: SeleniumCommandException | SeleniumCommandTimeoutException) -> None:
        error_messages = {
            SeleniumCommandException: "Ошибка выполнения команды Selenium",
            SeleniumCommandTimeoutException: "Таймаут команды Selenium",
        }
        
        error_message = error_messages.get(type(exception), "Неизвестная ошибка Selenium")
        await ShiftService._notify_admins_critical_error(error_type, error_message, exception)

    async def login(self) -> None:
        async with self._driver_mutex:
            try:
                self._selenium_client.close_driver()
                await self._selenium_client.start_process()
            except (SeleniumCommandException, SeleniumCommandTimeoutException) as e:
                await self._handle_selenium_error("Ошибка входа", e)
            except Exception as e:
                await self._notify_admins_critical_error("Неожиданная ошибка входа", str(e), e)

    async def find_new_shifts(self) -> list[ShiftBase]:
        async with self._driver_mutex:
            try:
                latest_shifts: dict[int, ShiftBase] = dict()
                shifts = await self._selenium_client.parse_shifts()
                
                for shift in shifts:
                    latest_shifts[shift.link] = shift
                
                if not len(latest_shifts):
                    logging.info("No shifts parsed from website")
                else:
                    logging.info(f"Successfully parsed {len(latest_shifts)} shifts")
                
                if len(self._existing_shift_links) > 0:
                    latest_shift_links = set(latest_shifts.keys())
                    new_shift_links = latest_shift_links - self._existing_shift_links
                    shift_list = set([latest_shifts[shift_link] for shift_link in new_shift_links])
                    for shift in shift_list:
                        shift.company = await self._selenium_client.parse_company_name(shift.link)
                    
                    self._existing_shift_links = latest_shift_links
                    return list(shift_list)
                else:
                    self._existing_shift_links = set(latest_shifts.keys())
                    return list()
            except SeleniumWebDriverNotReadyException:
                return []
            except (SeleniumCommandException, SeleniumCommandTimeoutException) as e:
                logging.error(f"Critical error in find_new_shifts: {e}")
                await self._handle_selenium_error("Ошибка поиска смен", e)
                return []
            except Exception as e:
                logging.error(f"Unexpected error in find_new_shifts: {e}")
                await self._notify_admins_critical_error("Неожиданная ошибка поиска смен", str(e), e)
                return []

    @staticmethod
    def format_shift_for_telegram(shift: ShiftBase) -> str:
        message_parts = []
        
        if shift.name:
            message_parts.append(f"🔄 {shift.name}")
        
        if shift.start and shift.end:
            start_time = shift.start.strftime("%d.%m.%Y %H:%M")
            end_time = shift.end.strftime("%d.%m.%Y %H:%M")
            duration = shift.end - shift.start
            hours = duration.total_seconds() / 3600
            message_parts.append(f"⏰: {start_time} - {end_time}")
            message_parts.append(f"⏱: {hours:.1f} часов")
        
        if shift.location:
            message_parts.append(f"📍: {shift.location}")

        if shift.company:
            message_parts.append(f"🏢: {shift.company}")
        
        if shift.position:
            message_parts.append(f"💼: {shift.position}")
        
        if shift.occupied is not None and shift.max_occupy is not None:
            message_parts.append(f"👥: {shift.occupied}/{shift.max_occupy}")
        elif shift.max_occupy is not None:
            message_parts.append(f"👥: {shift.max_occupy}")
        
        if shift.connected_shifts:
            message_parts.append(f"🔗: {len(shift.connected_shifts)}")
            for i, connected_shift in enumerate(shift.connected_shifts, 1):
                message_parts.append(f"\n📋 Смена {i}:")
                if connected_shift.name:
                    message_parts.append(f"   🔄 {connected_shift.name}")
                if connected_shift.start and connected_shift.end:
                    start_time = connected_shift.start.strftime("%d.%m.%Y %H:%M")
                    end_time = connected_shift.end.strftime("%d.%m.%Y %H:%M")
                    message_parts.append(f"  ⏰ {start_time} - {end_time}")
                if connected_shift.location:
                    message_parts.append(f"  📍 {connected_shift.location}")
                if connected_shift.company:
                    message_parts.append(f"  🏢 {connected_shift.company}")
                if connected_shift.position:
                    message_parts.append(f"  💼 {connected_shift.position}")
                if connected_shift.occupied is not None and connected_shift.max_occupy is not None:
                    message_parts.append(f"  👥 {connected_shift.occupied}/{connected_shift.max_occupy}")
        
        if shift.link:
            message_parts.append(f"\n🔗 Ссылка: https://shameless.sinch.cz/react/position/{shift.link}")
        
        return "\n".join(message_parts)

    @staticmethod
    def format_filter_for_telegram(filter_obj: FilterBase) -> str:
        message_parts = []
        
        list_type = "Чёрный список" if filter_obj.is_black_list else "Белый список"
        logic_type = "И (AND)" if filter_obj.is_and else "ИЛИ (OR)"
        message_parts.append(f"📋 {list_type} - {logic_type}")
        
        if filter_obj.companies:
            companies_list = ", ".join([company.value for company in filter_obj.companies])
            message_parts.append(f"🏢 Компании: {companies_list}")
        
        if filter_obj.locations:
            locations_list = ", ".join([location.value for location in filter_obj.locations])
            message_parts.append(f"📍 Локации: {locations_list}")
        
        if filter_obj.positions:
            positions_list = ", ".join([position.value for position in filter_obj.positions])
            message_parts.append(f"💼 Позиции: {positions_list}")
        
        if filter_obj.longer:
            hours = filter_obj.longer.total_seconds() / 3600
            message_parts.append(f"⏱️ Минимальная длительность: {hours:.1f} часов")
        
        if filter_obj.shorter:
            hours = filter_obj.shorter.total_seconds() / 3600
            message_parts.append(f"⏱️ Максимальная длительность: {hours:.1f} часов")
        
        if not any([filter_obj.companies, filter_obj.locations, filter_obj.positions, filter_obj.longer, filter_obj.shorter]):
            message_parts.append("📝 Фильтр пустой")
        
        return "\n".join(message_parts)

    @staticmethod
    def filter_new_shifts(shift_list: list[ShiftBase], shift_filter: FilterBase) -> list[ShiftBase]:
        final_shift_list = list()
        for shift in shift_list:
            if ShiftService._shift_matches_filter(shift, shift_filter):
                if len(
                        ShiftService.filter_new_shifts(shift.connected_shifts, shift_filter)
                ) != len(shift.connected_shifts):
                    continue
                final_shift_list.append(shift)
        return final_shift_list

    @staticmethod
    def _shift_matches_filter(shift: ShiftBase, shift_filter: FilterBase) -> bool:
        conditions = []
        
        if shift_filter.longer:
            conditions.append(shift_filter.longer < (shift.end - shift.start))

        if shift_filter.shorter:
            conditions.append(shift_filter.shorter > (shift.end - shift.start))

        if shift_filter.companies:
            company_values = [company.value for company in shift_filter.companies]
            conditions.append(shift.company and shift.company in company_values)

        if shift_filter.locations:
            location_values = [location.value for location in shift_filter.locations]
            conditions.append(shift.location in location_values)

        if shift_filter.positions:
            position_values = [position.value for position in shift_filter.positions]
            conditions.append(shift.position in position_values)
        
        if not conditions:
            return True
        
        if shift_filter.is_and:
            if shift_filter.is_black_list:
                return not all(conditions)
            else:
                return all(conditions)
        else:
            if shift_filter.is_black_list:
                return not any(conditions)
            else:
                return any(conditions)

    async def search(self) -> None:
        start_time = time.time()
        new_shifts = await self.find_new_shifts()

        # from datetime import datetime, timedelta
        # test_shift = ShiftBase(
        #     name="TEST SHIFT - Mute Test",
        #     start=datetime.now() + timedelta(hours=1),
        #     end=datetime.now() + timedelta(hours=5),
        #     location="Test Location",
        #     company="Test Company",
        #     occupied=0,
        #     max_occupy=1,
        #     link=999999,
        #     position="Test Position",
        #     is_bind=False,
        #     connected_shifts=[]
        # )
        # new_shifts.append(test_shift)

        logging.info(f"Found {len(new_shifts)} new shifts in {time.time() - start_time:.2f} seconds")

        active_users = await self._user_dao.get_users_with_active_access()
        if not active_users:
            logging.info("No active users found")
            return

        user_filters = await self._filter_dao.get_batch_user_filters([active_user.id for active_user in active_users])

        for user in active_users:
            filters = user_filters[user.id]
            user_shifts = copy.deepcopy(new_shifts)

            if len(filters) == 2:
                if filters[0].is_black_list:
                    user_shifts = ShiftService.filter_new_shifts(user_shifts, filters[1])
                    user_shifts = ShiftService.filter_new_shifts(user_shifts, filters[0])
                else:
                    user_shifts = ShiftService.filter_new_shifts(user_shifts, filters[0])
                    user_shifts = ShiftService.filter_new_shifts(user_shifts, filters[1])

            mute_service = MuteService.get_instance()
            user_mutes = await mute_service.get_batch_user_mutes([user.id])
            muted_shifts = user_mutes.get(user.id, set())

            for shift in user_shifts:
                if shift.link not in muted_shifts:
                    formatted_message = ShiftService.format_shift_for_telegram(shift)
                    mute_keyboard = shift_mute_keyboard(shift.link)
                    await MessageService.get_instance().send_message_specific_user(
                        user.tg_id,
                        message=formatted_message,
                        keyboard=mute_keyboard
                    )

    async def login_task(self) -> None:
        while True:
            await self.login()
            await asyncio.sleep(self._login_timeout * 60)

    async def mute_cleanup_task(self) -> None:
        while True:
            mute_service = MuteService.get_instance()
            await mute_service.cleanup_expired_mutes()
            await asyncio.sleep(self._mute_clean_timeout * 60)

    async def search_task(self) -> None:
        while True:
            await self.search()
            logging.info(f"Search task completed, sleeping for {self._search_timeout} seconds")
            await asyncio.sleep(self._search_timeout)

    async def run(self) -> None:
        try:
            self._login_task = asyncio.create_task(self.login_task())
            self._search_task = asyncio.create_task(self.search_task())
            self._mute_cleanup_task = asyncio.create_task(self.mute_cleanup_task())
        except Exception as e:
            await self._notify_admins_critical_error("Ошибка запуска сервиса", str(e), e)
            raise
