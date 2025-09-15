class MainMenuAction:
    FILTERS = "filters"
    SUBSCRIPTION = "subscription"
    MAIN_MENU = "main_menu"
    ADMIN_PANEL = "admin_panel"


class FilterAction:
    WHITE_LIST = "white_list"
    BLACK_LIST = "black_list"
    FILTERS_MENU = "filters_menu"


class ModifyFilterAction:
    ADD_RULE = "add_rule_"
    DELETE_RULE = "delete_rule_"
    MODIFY_MENU = "modify_menu_"
    SET_LOGIC = "set_logic_"


class AddFilterAction:
    ADD_COMPANY = "add_company_"
    ADD_LOCATION = "add_location_"
    ADD_POSITION = "add_position_"
    ADD_LONGER = "add_longer_"
    ADD_SHORTER = "add_shorter_"


class RemoveFilterAction:
    REMOVE_COMPANY = "remove_company_"
    REMOVE_LOCATION = "remove_location_"
    REMOVE_POSITION = "remove_position_"
    REMOVE_LONGER = "remove_longer_"
    REMOVE_SHORTER = "remove_shorter_"


class CallbackWithIdAction:
    REMOVE_POSITION = "act_remove_rule_position_"
    REMOVE_COMPANY = "act_remove_rule_company_"
    REMOVE_LOCATION = "act_remove_rule_location_"
    REMOVE_LONGER = "act_remove_rule_longer_"
    REMOVE_SHORTER = "act_remove_rule_shorter_"
    
    ADD_LONGER = "act_add_rule_longer_"
    ADD_SHORTER = "act_add_rule_shorter_"
    SELECT_POSITION = "select_position_"
    SET_IS_AND = "set_is_and_"
    MUTE_SHIFT = "mute_shift_"


class AdminPanelAction:
    VIEW_ALL_USERS = "view_all_users"
    VIEW_ACTIVE_USERS = "view_active_users"
    VIEW_ADMIN_USERS = "view_admin_users"
    GRANT_ADMIN = "grant_admin"
    REVOKE_ADMIN = "revoke_admin"
    ACTIVATE_USER = "activate_user"
    DEACTIVATE_USER = "deactivate_user"
    SEND_MESSAGE_TO_ALL = "send_message_to_all"
    BACK_TO_ADMIN_PANEL = "back_to_admin_panel"


DURATION_LIST = [2, 4, 6, 8, 10, 12]

POSITION_LIST = [
    "Stagehands - Záložník",
    "Stagehands - Pracovník", 
    "Stagehands - Crewboss"
]
    

