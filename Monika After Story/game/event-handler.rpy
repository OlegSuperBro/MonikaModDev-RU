# Module that defines functions for story event handling
# Assumes:
#   persistent.event_list
#   persistent.current_monikatopic

# current event list item data
default persistent._mas_curr_eli_data = None

# keep track of number of pool unlocks
default persistent._mas_pool_unlocks = 0

# NOTE: proof oc concept
# transform to have monika just chill
image monika_waiting_img:
    "monika 1eua"
    1.0
    "monika 1euc"
    1.0
    "monika 1esc"
    1.0
    "monika 1lksdlc"
    1.0
    "monika 1ekd"
    1.0
    repeat

# transform for monika's prompt waiting location
transform prompt_monika:
    tcommon(950,z=0.8)


init -999 python in mas_ev_data_ver:
    # must be before -900 so we can use in persistent backup/cleanup

    # need to use real lists and dicts here
    import builtins

    # special store dedicated to verification of Event-based data
    import datetime
    import renpy


    def _strict_can_pickle(val):
        """
        Checks if this value can be pickled safely into persistent.

        This is VERY strict. we only allow types, not isinstance checks.
        no ducks here

        This will check structures recursively and will catch recursion errors.

        IN:
            val - value to check

        RETURNS: tuple of the following format:
            [0] - True if the value can be safely pickled, False if recursion
                error or not picklable.
            [1] - True if recursion error, False otherwise
        """
        try:
            return __strict_can_pickle(val), False
        except RuntimeError as re:
            # yes, this how to check for recursion in python < 3.5
            # NOTE: this also handles renpy's recursion error
            #   (tom includes more text)
            if "maximum recursion depth exceeded" not in re.args[0]:
                raise
            return False, True


    def __strict_can_pickle(val):
        """
        Recursive strict pickle check. See _strict_can_pickle for more info.

        Will raise recursion error if appropriate.

        IN:
            val - value to check

        RETURNS: True if value can be safely pickled, False otherwise.
        """
        if val is None:
            return True

        # non-structure types
        val_type = type(val)
        if val_type in (
                str,
                unicode,
                bool,
                int,
                float,
                long,
                complex,
                datetime.timedelta,
                datetime.date,
        ):
            return True

        # time-based needs to have tzinfo none
        if val_type in (datetime.datetime, datetime.time):
            return val.tzinfo is None

        # list types
        if val_type in (
                __builtin__.list,
                renpy.python.RevertableList,
                __builtin__.set,
                __builtin__.frozenset,
                renpy.python.RevertableSet,
                tuple,
        ):
            for sub_val in val:
                if not __strict_can_pickle(sub_val):
                    return False
            return True

        # dict types
        if val_type in (__builtin__.dict, renpy.python.RevertableDict):
            for sub_key in val:
                if (
                        not __strict_can_pickle(sub_key)
                        or not __strict_can_pickle(val[sub_key])
                ):
                    return False
            return True

        # anything else probably bad
        return False


    ## verification type functions
    ## most of these lead into verify_item
    def _verify_bool(val, allow_none=True):
        return _verify_item(val, bool, allow_none)


    def _verify_dict(val, allow_none=True):
        return _verify_item(val, builtins.dict, allow_none)


    def _verify_list(val, allow_none=True):
        return _verify_item(val, builtins.list, allow_none)


    def _verify_dt(val, allow_none=True):
        if (
                isinstance(val, datetime.datetime)
                and val.year < 1900
            ):
            return False
        return _verify_item(val, datetime.datetime, allow_none)


    def _verify_dt_nn(val):
        return _verify_dt(val, False)


    def _verify_evact(val, allow_none=True):
        if val is None:
            return allow_none

        return val in store.EV_ACTIONS


    def _verify_int(val, allow_none=True):
        return _verify_item(val, int, allow_none)


    def _verify_int_nn(val):
        return _verify_int(val, False)


    def _verify_str(val, allow_none=True):
        if val is None:
            return allow_none

        return isinstance(val, str) or isinstance(val, unicode)


    def _verify_td(val, allow_none=True):
        if val is None:
            return allow_none
        return _verify_item(val, datetime.timedelta, allow_none)


    def _verify_td_nn(val):
        return _verify_td(val, False)


    def _verify_tuli(val, allow_none=True):
        if val is None:
            return allow_none

        return isinstance(val, builtins.list) or isinstance(val, tuple)


    def _verify_tuli_nn(val):
        return _verify_tuli(val, False)


    def _verify_tuli_aff(val, allow_none=True):
        if val is None:
            return allow_none

        return isinstance(val, tuple) and len(val) == 2


    def _verify_item(val, _type, allow_none=True):
        """
        Verifies the given value has the given type/instance

        IN:
            val - value to verify
            _type - type to check
            allow_none - If True, None should be considered good value,
                false means bad value
                (Default: True)

        RETURNS: True if the given value has the given type/instance,
            false otherwise
        """
        if val is None:
            return allow_none

        # otherwise check item
        return isinstance(val, _type)


    class MASCurriedVerify(object):
        """
        Allows for currying of a verification function
        """

        def __init__(self, verifier, allow_none):
            """
            Constructor

            IN:
                verifier - the verification function we want to use
                allow_none - True if we should pass True for allow_none,
                    false for False
            """
            self.verifier = verifier
            self.allow_none = allow_none


        def __call__(self, value):
            """
            Callable override

            IN:
                value - the value we want to verify

            RETURNS: True if the value passes verification, False otherwise
            """
            return self.verifier(value, self.allow_none)


init -998 python in mas_ev_data_ver:
    import time
    import renpy
    import store

    def _verify_per_mtime():
        """
        verifies persistent data and ensure mod times are not in the future
        """
        curr_time = time.time()

        # check renpy persistent mtime
        if renpy.persistent.persistent_mtime > curr_time:
            renpy.persistent.persistent_mtime = curr_time

        # then save location mtime
        if renpy.loadsave.location is not None:
            locs = renpy.loadsave.location.locations
            if locs is not None and len(locs) > 0 and locs[0] is not None:
                if locs[0].persistent_mtime > curr_time:
                    locs[0].persistent_mtime = curr_time

        # then individual mtimes
        for varkey in store.persistent._changed:
            if store.persistent._changed[varkey] > curr_time:
                store.persistent._changed[varkey] = curr_time

    # verify
    try:
        _verify_per_mtime()
        valid_times = True
    except:
        valid_times = False
        store.mas_utils.mas_log.error("[EARLY]: Failed to verify mtimes")

init -950 python in mas_ev_data_ver:
    import store

    # map data to tuples
    _verify_map = {
        0: MASCurriedVerify(_verify_str, False), # eventlabel
        1: MASCurriedVerify(_verify_str, True), # prompt
        2: MASCurriedVerify(_verify_str, True), # label
        # TODO: because of reactions, we cannot verify category yet
#        3: MASCurriedVerify(_verify_tuli, True), # category
        4: MASCurriedVerify(_verify_bool, True), # unlocked
        5: MASCurriedVerify(_verify_bool, True), # random
        6: MASCurriedVerify(_verify_bool, True), # pool
        7: MASCurriedVerify(_verify_str, True), # conditional
        8: MASCurriedVerify(_verify_evact, True), # action
        9: MASCurriedVerify(_verify_dt, True), # start_date
        10: MASCurriedVerify(_verify_dt, True), # end_date
        11: MASCurriedVerify(_verify_dt, True), # unlock_date
        12: MASCurriedVerify(_verify_int, False), # shown_count
        #13: MASCurriedVerify(_verify_str, True), # diary_entry
        14: MASCurriedVerify(_verify_dt, True), # last_seen
        15: MASCurriedVerify(_verify_tuli, True), # years
        16: MASCurriedVerify(_verify_bool, True), # sensitive
        17: MASCurriedVerify(_verify_tuli_aff, True), # aff_range
        18: MASCurriedVerify(_verify_bool, True), # show_in_idle
    }


    def _verify_data_line(ev_line):
        """
        Verifies event data for a single tuple of data.

        IN:
            ev_line - single line of data to verify

        RETURNS:
            True if passed verification, False if not
        """
        # we only want to check what exists in this data
        for index in range(len(ev_line)):
            # go through verification map and verify
            verify = _verify_map.get(index, None)
            if verify is not None and not verify(ev_line[index]):
                # verification failed!
                return False

        return True


    def verify_event_data(per_db):
        """
        Verifies event data of the given persistent data. Entries that are
        invalid are removed. We only check the bits of data that we have, so
        data lines with smaller sizes are only validated for what they have.

        IN:
            per_db - persistent database to verify
        """
        if per_db is None:
            return

        for ev_label in tuple(per_db.keys()):
            # pull out the data
            ev_line = per_db[ev_label]

            if not _verify_data_line(ev_line):
                # verification failed! pop this element
                store.mas_utils.mas_log.error(
                    "bad data found in {0}".format(ev_label)
                )
                per_db.pop(ev_label)


init -895 python in mas_ev_data_ver:
    # this MUST happen after the data migrations

    # verify some databases
    for _dm_db in store._mas_dm_dm.per_dbs:
        verify_event_data(_dm_db)

    _dm_db = None
#    verify_event_data(store.persistent.event_database)
#    verify_event_data(store.persistent._mas_compliments_database)
#    verify_event_data(store.persistent.farewell_database)
#    verify_event_data(store.persistent.greeting_database)
#    verify_event_data(store.persistent._mas_mood_database)
#    verify_event_data(store.persistent._mas_story_database)
#    verify_event_data(store.persistent._mas_apology_database)


init -500 python:
    # initalies the locks db

    # the template is the regular starter case for most events
    # True means that the property is locked on startup (wont change),
    # False means it is unlocked (will change)
    mas_init_lockdb_template = (
        True, # event label
        False, # prompt
        False, # label
        False, # category
        True, # unlocked
        True, # random
        True, # pool
        True, # conditional
        True, # action
        True, # start_date
        True, # end_date
        True, # unlock_date
        True, # shown_count
        False, # diary_entry
        True, # last_seen
        False, # years
        False, # sensitive
        False, # aff_range
        False, # show_in_idle
    )

    # NOTE: aff_range is unlocked because making adjustments to topics would
    #   become really difficult if we just kept this locked

    # set defaults
#    if (
#            persistent._mas_event_init_lockdb_template is not None
#            and len(persistent._mas_event_init_lockdb_template)
#                != len(mas_init_lockdb_template)
#        ):
        # differing lengths mean we have new items to deal with

    # set db defaults
    if persistent._mas_event_init_lockdb is None:
        persistent._mas_event_init_lockdb = dict()

    for ev_key in persistent._mas_event_init_lockdb:
        stored_lock_row = persistent._mas_event_init_lockdb[ev_key]

        if len(mas_init_lockdb_template) != len(stored_lock_row):
            # splice and dice
            lock_row = list(mas_init_lockdb_template)
            lock_row[0:len(stored_lock_row)] = list(stored_lock_row)
            persistent._mas_event_init_lockdb[ev_key] = tuple(lock_row)

    # set the new template
    persistent._mas_event_init_lockdb_template = mas_init_lockdb_template

    # set db defaults
#    if persistent._mas_event_init_lockdb is None:
#        persistent._mas_event_init_lockdb = dict()

    # initalizes LOCKDB for the Event class
    Event.INIT_LOCKDB = persistent._mas_event_init_lockdb



init 4 python:

    # ev reset handling
#    if persistent._mas_ev_reset_date is None:
#        persistent._mas_ev_reset_date = datetime.date.today()

#    else:
        #


    # the mapping is built here so events can use to build
    # map databses to a code
    mas_all_ev_db_map = {
        "EVE": store.evhand.event_database,
        "BYE": store.evhand.farewell_database,
        "GRE": store.evhand.greeting_database,
        "MOO": store.mas_moods.mood_db,
        "STY": store.mas_stories.story_database,
        "CMP": store.mas_compliments.compliment_database,
        "FLR": store.mas_filereacts.filereact_db,
        "APL": store.mas_apology.apology_db,
        "WRS": store.mas_windowreacts.windowreact_db,
        "FFF": store.mas_fun_facts.fun_fact_db,
        "SNG": store.mas_songs.song_db,
        "GME": store.mas_games.game_db
    }


init 6 python:
    # here we combine the data from teh databases so we can have easy lookups.

    # mainly to create centralized database for calendar lookup
    # (and possible general db lookups)
    mas_all_ev_db = {}
    for code,ev_db in mas_all_ev_db_map.items():
        mas_all_ev_db.update(ev_db)

    del code, ev_db


    class MAS_EVL(object):
        """
        Context manager wrapper for Event objects via event labels.
        This has handling for when an eventlabel doesn't return an actual
        event object via mas_getEV.

        Use as follows:
            with MASev('some event label') as ev:
                ev.<property name> = new_value
                curr_value ev.<property_name>

        property names should be same as used on Event object.
        functions can also be used.
        additionally, the resulting context object can be compared with
        other event objects like normal.

        In cases where the Event does not exist, the following occurs:
            - Event properties return their defaults (see below)
            - property set operations do nothing
            - functions calls do nothing
            - The Event class is used as fallback
        """
        _default_values = {
            "eventlabel": "",
            "prompt": None,
            "label": None,
            "category": None,
            "unlocked": False,
            "random": False,
            "pool": False,
            "conditional": None,
            "action": None,
            "start_date": None,
            "end_date": None,
            "unlock_date": None,
            "shown_count": 0,
            "last_seen": None,
            "years": None,
            "sensitive": False,
            "aff_range": None,
            "show_in_idle": False,
            "flags": 0,
        }

        _null_dicts = {
            "per_eventdb": 0,
            "rules": 0,
        }

        def __init__(self, evl):
            """
            Constructor

            IN:
                evl - event label to build context manager for
            """
            self._ev = mas_getEV(evl)

        def __repr__(self):
            return repr(self._ev)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False # always propagate exceptions

        def __getattr__(self, name):
            if self._ev is None:

                # event props
                if name in MAS_EVL._default_values:
                    return MAS_EVL._default_values.get(name)

                # event props where we dont want static vars to collide
                if name in MAS_EVL._null_dicts:
                    return {}

                if callable(Event.__dict__.get(name)):
                    # functions (on object, not class)
                    return MASDummyClass()

                # everything else gets whatever we have in event
                return getattr(Event, name)

            return getattr(self._ev, name)

        def __setattr__(self, name, value):
            if name == "_ev":
                self.__dict__["_ev"] = value

            elif self._ev is None:
                return

            elif self._ev is not None:
                setattr(self._ev, name, value)

            else:
                super(self, MAS_EVL).__setattr__(name, value)

        def __eq__(self, other):
            if self._ev is None:
                return False
            if isinstance(other, Event):
                return self._ev == other
            return False

        def __ne__(self, other):
            if self._ev is None:
                return False
            return not self.__eq__(other)


    def mas_getEV(ev_label):
        """
        Global get function that retreives an event given the label

        Designed to be used as a wrapper around the mas_all_ev_db dict
        NOTE: only available at RUNTIME

        IN:
            ev_label - eventlabel to find event for

        RETURNS:
            the event object you were looking for, or None if not found
        """
        return mas_all_ev_db.get(ev_label, None)

    def mas_checkEVL(ev_label, predicate):
        """
        Checks event properties using a lambda

        IN:
            ev_label - ev_label representing the event to check properties for
            predicate - predicate function (accepting an ev as the argument) for the test(s)

        OUT:
            True if predicate function returns True, False otherwise

        NOTE: Does nothing if the ev does not exist
        """
        ev = mas_getEV(ev_label)

        if ev is None:
            return False

        return predicate(ev)

    def mas_getEVLPropValue(ev_label, prop, default=None):
        """
        Safely gets an ev prop value

        IN:
            ev_label - eventlabel corresponding to the event object to get the property from
            prop - property name to get
            default - default value to return if ev not found/prop not found
                (Default: None)

        OUT:
            Value of the given property name, or default if not found/no ev exists
        """
        ev = mas_getEV(ev_label)

        return getattr(ev, prop, default)

    def mas_setEVLPropValues(ev_label, **kwargs):
        """
        Sets ev prop values in bulk if the ev exists

        IN:
            ev_label - ev_label representing the event to set properties for
            kwargs - propname=new_value. Represents the value to set to the property

        OUT:
            True if the property/ies was/were set
            False if not (ev does not exist)
        """
        ev = mas_getEV(ev_label)

        if ev is None:
            return False

        for attr, new_value in kwargs.items():
            setattr(ev, attr, new_value)

        return True

    def mas_isPoolEVL(ev_label):
        """
        Checks if the event for the given event label is pool

        IN:
            ev_label - eventlabel corresponding to the event we wish to check if is pooled

        OUT:
            True if the ev is pooled, False if not, or the ev doesn't exist
        """
        return mas_getEVLPropValue(ev_label, "pool", False)

    def mas_isRandomEVL(ev_label):
        """
        Checks if the event for the given event label is random

        IN:
            ev_label - eventlabel corresponding to the event we wish to check if is random

        OUT:
            True if the ev is random, False if not, or the ev doesn't exist
        """
        return mas_getEVLPropValue(ev_label, "random", False)

    def mas_isUnlockedEVL(ev_label):
        """
        Checks if the event for the given event label is unlocked

        IN:
            ev_label - eventlabel corresponding to the event we wish to check if is unlocked

        OUT:
            True if the ev is unlocked, False if not, or the ev doesn't exist
        """
        return mas_getEVLPropValue(ev_label, "unlocked", False)

    def mas_getEVL_last_seen(ev_label, default=None):
        """
        Gets the last_seen from the event corresponding to the given eventlabel

        If the event doesn't exist, the default is returned

        IN:
            ev_label - eventlabel for the event we wish to get last_seen from
            default - value to return if the event object doesn't exist

        OUT:
            The last_seen of the ev, or the default if the event doesn't exist
        """
        return mas_getEVLPropValue(ev_label, "last_seen", default)

    def mas_getEVL_shown_count(ev_label, default=0):
        """
        Gets the shown_count from the event corresponding to the given eventlabel

        If the event doesn't exist, the default is returned

        IN:
            ev_label - eventlabel for the event we wish to get shown_count from
            default - value to return if the event object doesn't exist

        OUT:
            The shown_count of the ev, or the default if the event doesn't exist
        """
        return mas_getEVLPropValue(ev_label, "shown_count", default)

    def mas_inRulesEVL(ev_label, *args):
        """
        Checks if keys are in the event's rules dict

        IN:
            ev_label - eventlabel for the event we wish to check rule keys for
            *args - rule keys

        OUT:
            True if all rule keys provided are in an event object's rules dict
            False if the event doesn't exist or any provided keys aren't present in the rules dict
        """
        ev_rules = mas_getEVLPropValue(ev_label, "rules", dict())

        if not ev_rules:
            return False

        for rule_key in args:
            if rule_key not in ev_rules:
                return False
        return True

    def mas_assignModifyEVLPropValue(ev_label, propname, operation, value):
        """
        Does an assign-modify operation

        IN:
            ev_label - eventlabel representing the event that will have a property assign/modified
            propname - property name to do the assign-modify operation on
            operation - operator to assign/modify with. (Any of the following: +=, -=, *=, /= (as a string))
            value - value to use in the operation

        OUT:
            True if event values were assign/modified successfully
            False otherwise
        """
        ev = mas_getEV(ev_label)
        if not ev:
            return False

        else:
            try:
                exec("ev.{0} {1} {2}".format(propname, operation, value))
            except:
                return False
        return True

    def mas_getEVCL(ev_label):
        """
        Global get function that retrieves the calendar label for an event
        given the eventlabel. This is mainly to help with calendar.

        IN:
            ev_label - eventlabel to find calendar label for

        RETURNS:
            the calendar label you were looking for, or "Unknown Event" if
            not found.
        """
        ev = mas_getEV(ev_label)
        if ev is None:
            return "Unknown Event"
        else:
            return ev.label


    def mas_hideEVL(
            ev_label,
            code,
            lock=False,
            derandom=False,
            depool=False,
            decond=False
        ):
        """
        Hides an event given label and code.

        IN:
            ev_label - label of event to hide
            code - string code of the db this ev_label belongs to
            lock - True if we want to lock this event
                (Default: False)
            derandom - True if we want to de random this event
                (Default: False)
            depool - True if we want to de pool this event
                (Default: False)
            decond - True if we want to remove conditoinal for this event
                (Default: False)
        """
        store.evhand._hideEvent(
            mas_all_ev_db_map.get(code, {}).get(ev_label, None),
            lock=lock,
            derandom=derandom,
            depool=depool,
            decond=decond
        )


    def mas_showEVL(
            ev_label,
            code,
            unlock=False,
            _random=False,
            _pool=False,
        ):
        """
        Shows an event given label and code.

        IN:
            ev_label - label of event to show
            code - string code of the db this ev_label belongs to
            unlock - True if we want to unlock this Event
                (Default: False)
            _random - True if we want to random this event
                (Default: False)
            _pool - True if we want to random thsi event
                (Default: False)

        NOTE:
            if using this to random, it does not protect labels that are in persistent._mas_player_derandomed
            and thus will remove the label from that list if present.

            if the label should not be randomed if it's in persistent._mas_player_derandomed
            use mas_protectedShowEVL
        """

        if _random:
            store.mas_bookmarks_derand.removeDerand(ev_label)

        store.mas_showEvent(
            mas_all_ev_db_map.get(code, {}).get(ev_label, None),
            unlock=unlock,
            _random=_random,
            _pool=_pool
        )

    def mas_protectedShowEVL(
            ev_label,
            code,
            unlock=False,
            _random=False,
            _pool=False,
        ):
        """
        Shows an event given label and code.

        Does checking if the actions should happen
        IN:
            ev_label - label of event to show
            code - string code of the db this ev_label belongs to
            unlock - True if we want to unlock this Event
                (Default: False)
            _random - True if we want to random this event
                (Default: False)
            _pool - True if we want to random thsi event
                (Default: False)
        """
        mas_showEVL(
            ev_label=ev_label,
            code=code,
            unlock=unlock,
            _random=_random and store.mas_bookmarks_derand.shouldRandom(ev_label),
            _pool=_pool
        )

    def mas_lockEVL(ev_label, code):
        """
        Locks an event given label and code.

        IN:
            ev_label - label of event to show
            code - string code of the db this ev_label belongs to
        """
        mas_hideEVL(ev_label, code, lock=True)


    def mas_unlockEVL(ev_label, code):
        """
        Unlocks an event given label and code.

        IN:
            ev_label - label of event to show
            code - string code of the db this ev_label belongs to
        """
        mas_showEVL(ev_label, code, unlock=True)


    def mas_stripEVL(ev_label, list_pop=False, remove_dates=True):
        """
        Strips the conditional and action properties from an event given its label
        start_date and end_date will be removed if remove_dates is True
        Also removes the event from the event list if present (optional)

        IN:
            ev_label - label of event to strip
            list_pop - True if we want to remove the event from the event list
                (Default: False)
            remove_dates - True if we want to remove start/end_dates from the event
                (Default: True)
        """
        if remove_dates:
            mas_setEVLPropValues(
                ev_label,
                conditional=None,
                action=None,
                start_date=None,
                end_date=None
            )

        else:
            mas_setEVLPropValues(
                ev_label,
                conditional=None,
                action=None
            )

        if list_pop:
            mas_rmEVL(ev_label)


    def mas_flagEVL(ev_label, code, flags):
        """
        Applies flags to the given event

        IN:
            ev_label - label of the event to flag
            code - string code of the db this ev_label belongs to
            flags - flags to apply
        """
        ev = mas_all_ev_db_map.get(code, {}).get(ev_label, None)
        if ev is not None:
            ev.flag(flags)


    def mas_unflagEVL(ev_label, code, flags):
        """
        Unflags flags from the given event

        IN:
            ev_label - label of the event to unflag
            code - string code of the db this ev_label belongs to
            flags - flags to unset
        """
        ev = mas_all_ev_db_map.get(code, {}).get(ev_label, None)
        if ev is not None:
            ev.unflag(flags)


init 4 python:
    def mas_lastSeenInYear(ev_label, year=None):
        """
        Checks whether or not the even was last seen in the year provided

        IN:
            ev_label - label of the event we want to check
            year - the year we want to check if it's been last seen in

        OUT:
            boolean - True if last seen this year, False otherwise

        NOTE: if no year provided, we assume this year
        """
        #Get our ev
        try:
            #NOTE: try/except because of init time conditional checks
            ev = mas_getEV(ev_label)
        except:
            ev = None

        #If we can't get the ev or it hasn't been seen before, then we can't do anything and we'll just return False
        if not ev or not ev.last_seen:
            return False

        #If no year provided, assume current year
        if year is None:
            year = datetime.date.today().year

        #Otherwise return this evaluation
        return ev.last_seen.year == year

    def mas_lastSeenLastYear(ev_label):
        """
        Checks if the event corresponding to ev_label was last seen last year
        """
        return mas_lastSeenInYear(ev_label, datetime.date.today().year-1)

    # clean yearset
    store.evhand.cleanYearsetBlacklist()


python early:
    # FLOW CHECK CONSTANTS
    # these define where in game flow should a delayed action be checked
    # these are bit based so you can define multiple using bitwise operations

    # checked during init process
    # NOTE: this is at runlevel 995
    # AKA after the all event database has been built
    MAS_FC_INIT = 1

    # checked during runtime start (aka splash)
    MAS_FC_START = 2

    # checked at end of game (aka quit)
    MAS_FC_END = 4

    # checked during idle, roughly every minute
    MAS_FC_IDLE_ROUTINE = 8

    # checked during idle, only once per session
    # NOTE: in other words, only check when we enter spcaeroom
    MAS_FC_IDLE_ONCE = 16

    # checked during idle, once per hour
    MAS_FC_IDLE_HOUR = 32

    # checked during idle, once per day
    MAS_FC_IDLE_DAY = 64

    MAS_FC_CONSTANTS = [
        MAS_FC_INIT,
        MAS_FC_START,
        MAS_FC_END,
        MAS_FC_IDLE_ROUTINE,
        MAS_FC_IDLE_ONCE,
        MAS_FC_IDLE_HOUR,
        MAS_FC_IDLE_DAY,
    ]


init -880 python:
    # THE DELAYED ACTION MAP
    # this is the one we actually use when running stuff
    # please note that this is internal use only.
    # right below this is the class definition that should be used for general
    # purpose
    if persistent._mas_delayed_action_list is None:

        # this list will only contain DelayedAction IDs
        # we will match these IDs using the delayed action map.
        persistent._mas_delayed_action_list = list()

    # the runtime version of this list is actually a dict
    # key: ID of the delayed action
    # value: the DelayedAction to perform
    mas_delayed_action_map = dict()

    class MASDelayedAction(object):
        """
        A Delayed action consists of the following:

        All exceptions are logged

        id - the unique ID of this DelayedAction
        ev - the event this action is associated with
        conditional - the logical conditional we want to check before performing
            action
            NOTE: this is not checked for correctness
            If cond_is_callable is True, then this is called instead of eval'd.
            In that case, the event object in question is passed into the
            callable.
        action - EV_ACTION constant this delayed action will perform
            NOTE: this is not checked for existence
            NOTE: this can also be a callable
                the event would be passd in as ev
                if callable, make this return True upon success and false
                    othrewise
        flowcheck - FC constant saying when this delayed action should be
            checked
            NOTE: this is not checked for existence
        been_checked - True if this action has been checked this game session
        executed - True if this delayed action has been executed
            - Delayed actions that have been executed CANNOT be executed again
        cond_is_callable - True if the conditional is a callable instead of
            a eval check.
            NOTE: we do not check callable for correctness
        """
        ERR_COND = "delayed action has bad conditional '{0}' | {1}"


        def __init__(self,
                _id,
                ev,
                conditional,
                action,
                flowcheck,
                cond_is_callable=False
            ):
            """
            Constructor

            NOTE: MAY raise exceptions
            NOTE: also logs exceptions.

            IN:
                _id - id of this delayedAction
                ev - event this action is related to
                conditional - conditional to check to do this action
                    NOTE: if this is a callable, then event is passed in
                action - EV_ACTION constant for this delayed action
                    NOTE: this can also be a callable
                        ev would be passed in as ev
                    If callable, make this return True on success, False
                        otherwise
                flowcheck - FC constant saying when this delaeyd action should
                    be checked
                cond_is_callable - True if the conditional is actually a
                    callable.
                    If this True and None is passed into the conditional, then
                    we just return False (aka never run the delayedaction)
                    (Default: False)
            """
            if not cond_is_callable:
                try:
                    eval(conditional)
                except Exception as e:
                    store.mas_utils.mas_log.error(self.ERR_COND.format(
                        conditional,
                        str(e)
                    ))
                    raise e

            self.cond_is_callable = cond_is_callable
            self.conditional = conditional
            self.action = action
            self.flowcheck = flowcheck
            self.been_checked = False
            self.executed = False
            self.ev = ev
            self.id = _id


        def __call__(self):
            """
            Checks if the conditional passes then performs the action

            NOTE: logs exceptions

            RETURNS:
                True on successful action performed, False otherwise
            """
            # NO event? dont even do this
            if self.ev is None or self.executed or self.action is None:
                return False

            # this should already have been checked on start
            try:

                # test conditional
                if self.cond_is_callable:

                    if self.conditional is None:
                        # no conditional, then we dont do anything
                        return False

                    condition_passed = self.conditional(ev=self.ev)

                else:
                    condition_passed = eval(self.conditional)

                # run event if condition passed
                if condition_passed:
                    if self.action in Event.ACTION_MAP:
                        Event.ACTION_MAP[self.action](
                            self.ev, unlock_time=datetime.datetime.now()
                        )
                        self.executed = True

                    else:
                        # action must be a callable
                        self.executed = self.action(ev=self.ev)

            except Exception as e:
                store.mas_utils.mas_log.error(self.ERR_COND.format(
                    self.conditional,
                    str(e)
                ))
#                raise e

            return self.executed


        @staticmethod
        def makeWithLabel(
                _id,
                ev_label,
                conditional,
                action,
                flowcheck,
                cond_is_callable=False
            ):
            """
            Makes a MASDelayedAction using an eventlabel instead of an event

            IN:
                _id - id of this delayedAction
                ev_label - label of the event this action is related to
                conditional - conditional to check to do to tihs action
                action - EV_ACTION constant for this delayed action
                    NOTE: this can also be a cllable
                        ev would be passed in as ev
                    If callable, make this return True on success, False
                        otherwise
                flowcheck - FC constant saying when this delayed action should
                    be checked
                cond_is_callable - True if the conditional is actually a
                    callable.
                    If this True and None is passed into the conditional, then
                    we just return False (aka never run the delayedaction)
                    (Default: False)
            """
            return MASDelayedAction(
                _id,
                mas_getEV(ev_label),
                conditional,
                action,
                flowcheck,
                cond_is_callable
            )


    # now for helper functions for working with delayed actions
    def mas_removeDelayedAction(_id):
        """
        Removes a delayed action with the given ID

        NOTE: this removes from both persistent and the runtime lists

        IN:
            _id - id of the delayed action to remove
        """
        if _id in persistent._mas_delayed_action_list:
            persistent._mas_delayed_action_list.remove(_id)

        if _id in mas_delayed_action_map:
            mas_delayed_action_map.pop(_id)


    def mas_removeDelayedActions_list(_ids):
        """
        Removes a list of delayed actions with given Ids

        IN:
            _ids - list of Ids to remove
        """
        for _id in _ids:
            mas_removeDelayedAction(_id)


    def mas_removeDelayedActions(*args):
        """
        Multiple argument delayed action removal

        Assumes all given args are IDS
        """
        mas_removeDelayedActions_list(args)


    def mas_runDelayedActions(flow):
        """
        Attempts to run currently held delayed actions for the given flow mode

        Delayed actions that are successfully completed are removed from the
        list

        IN:
            flow - FC constant for the current flow
        """
        if flow not in MAS_FC_CONSTANTS:
            return

        # otherwise, lets try going thru the list
        for action_id in list(mas_delayed_action_map):
            action = mas_delayed_action_map[action_id]

            # bitcheck the flow
            if (action.flowcheck & flow) > 0:
                if action():
                    # then pop the item if it was successful
                    mas_removeDelayedAction(action_id)

                # we have now checked this action
                action.been_checked = True


    def mas_addDelayedAction(_id):
        """
        Creates a delayed action with the given ID and adds it to the delayed
        action map (runtime)

        NOTE: this handles duplicates, so its better to use this

        NOTE: this also adds to persistent, just in case

        IN:
            _id - id of the delayed action to create
        """
        if _id in mas_delayed_action_map:
            return

        # otherwise, lets get the constructor for the delayedaction
        make_action = store.mas_delact.MAP.get(_id, None)
        if make_action is None:
            return

        # we have a constructor, lets create!
        mas_delayed_action_map[_id] = make_action()

        # and lastlty, check persistent as well
        if _id not in persistent._mas_delayed_action_list:
            persistent._mas_delayed_action_list.append(_id)


    def mas_addDelayedActions_list(_ids):
        """
        Creates delayed actions given a list of Ids

        IN:
            _ids - list of IDS to add
        """
        for _id in _ids:
            mas_addDelayedAction(_id)


    def mas_addDelayedActions(*args):
        """
        Creates delayed actions given ids as args

        assumes each arg is a valid id
        """
        mas_addDelayedActions_list(args)


init 995 python:
    # this is where we run the init level batch of delayed actions
    mas_runDelayedActions(MAS_FC_INIT)

init -880 python in mas_delact:
    # we can assume store is imported for all mas_delacts
    import store

    def _MDA_safeadd(*ids):
        """
        Adds MASDelayedAction ids to the persistent mas delayed action list.

        NOTE: this is only meant for code that runs super early yet needs to
        add MASDelayedActions.

        NOTE: This will NOT add duplicates.

        IN:
            ids - ids to add to the delayed action list
        """
        for _id in ids:
            if _id not in store.persistent._mas_delayed_action_list:
                store.persistent._mas_delayed_action_list.append(_id)


    def _MDA_saferm(*ids):
        """
        Removes MASDelayedActions from the persistent mas delayed action list.

        NOTE: this is only meant for code that runs super early yet needs to
        remove MASDelayedActions

        NOTE: this will check for existence before removing

        IN:
            ids - ids to remove from the delayed action list
        """
        for _id in ids:
            if _id in store.persistent._mas_delayed_action_list:
                store.persistent._mas_delayed_action_list.remove(_id)


init -875 python in mas_delact:
    # store containing a map for delayed action mapping
    import datetime # for use in later functions

    # delayed action map:
    # key: ID of the delayed action
    # value: function to call that will generate the delayed action object
    #   NOTE: this function MUST be runnable at init level 995.
    #   NOTE: the result delayedaction does NOT have to be runnable at 995.
    MAP = {
        # NOTE: commented IDs have been retired
        # 1: _greeting_ourreality_unlock,
        # 2: _mas_monika_islands_unlock,
        # 3: _mas_bday_postbday_notimespent_reset,
        # 4: _mas_bday_pool_happy_bday_reset,
        # 5: _mas_bday_surprise_party_cleanup_reset,
        # 6: _mas_bday_surprise_party_hint_reset,
        # 7: _mas_bday_spent_time_with_reset,
        # 8: _mas_d25_holiday_intro_upset_reset,
        # 9: _mas_d25_monika_carolling_reset,
        # 10: _mas_d25_monika_mistletoe_reset,
        # 11: _mas_pf14_monika_lovey_dovey_reset,
        # 12: _mas_f14_monika_vday_colors_reset,
        # 13: _mas_f14_monika_vday_cliches_reset,
        # 14: _mas_f14_monika_vday_chocolates_reset,
        # 15: _mas_f14_monika_vday_origins_reset,
        16: _mas_birthdate_bad_year_fix,
    }


init 994 python in mas_delact:

    # this is also where we initialize the delayed action map
    def loadDelayedActionMap():
        """
        Checks the persistent delayed action list and generates the
        runtime map of delayed actions
        """
        store.mas_addDelayedActions_list(
            store.persistent._mas_delayed_action_list
        )


    def saveDelayedActionMap():
        """
        Checks the runtime map of delayed actions and saves them into the
        persistent value.

        NOTE: this does not ADD to the persistent's list. This recreates it
            entirely.
        """
        store.persistent._mas_delayed_action_list = [
            action_id for action_id in store.mas_delayed_action_map
        ]


    # now run the init
    loadDelayedActionMap()


default persistent._mas_ev_yearset_blacklist = {}
# key: label of the ev to reset yeras
# value: datetime that this blacklist expires

init -1 python in evhand:
    import store
    import re

    # this is the event database
    event_database = dict()
    farewell_database = dict()
    greeting_database = dict()

    # special namedtuple type we are using
    from collections import namedtuple

    # used to keep track of menu items in displaying the prompts.
    # menu -> menu to display for this pane
    # cats -> categories this menu has
    _NT_CAT_PANE = namedtuple("_NT_CAT_PANE", "menu cats")

    # RIGHT PANE
#    PREV_X = 30
    RIGHT_X = 1020
#    PREV_Y = 10
    RIGHT_Y = 15 + 55
#    PREV_W = 300
    RIGHT_W = 250
    RIGHT_H = 572
#    PREV_XALIGN = -0.08
    RIGHT_XALIGN = -0.10
    RIGHT_AREA = (RIGHT_X, RIGHT_Y, RIGHT_W, RIGHT_H)

    # LEFT PANE
#    MAIN_X = 360
    LEFT_X = 740
#    MAIN_Y = 10
    LEFT_Y = RIGHT_Y
#    MAIN_W = 300
    LEFT_W = RIGHT_W
    LEFT_H = RIGHT_H
#    MAIN_XALIGN = -0.08
    LEFT_XALIGN = -0.10
    LEFT_AREA = (LEFT_X, LEFT_Y, LEFT_W, LEFT_H)
    LEFT_EXTRA_SPACE = 68

    # time stuff
    import datetime
    LAST_SEEN_DELTA = datetime.timedelta(hours=6)

    # restart topic blacklist
    RESTART_BLKLST = []

    # idle topic whitelist
    IDLE_WHITELIST = [
        "unlock_prompt",
    ]

    # A base for search patterns that expect a string of the "key: value" kind
    # Use the key and value named indexes for substitution accordingly
    RET_KEY_PATTERN_BASE = (
        r"(?:(?<=\|)|(?<=^))\s*"# Start
        r"{key}"# Key
        r"\s*:\s*"# Separator
        r"{value}"# Value
        r"\s*(?:(?=\|)|(?=$))"# End
    )
    # Used to catch "idle_exp: EXP, DURATION" or "idle_exp: TAG" where DURATION is an int (seconds) and TAG is a string
    RET_KEY_PATTERN_IDLE_EXP = re.compile(
        RET_KEY_PATTERN_BASE.format(
            key=r"idle_exp",
            value=r"(?:(?P<exp>\d[a-z]{3,13})\s*,\s*(?P<duration>\d+)|(?P<tag>\w+))"
        )
    )
    # Used to catch "pause: DURATION" where DURATION is an int (seconds)
    RET_KEY_PATTERN_PAUSE = re.compile(
        RET_KEY_PATTERN_BASE.format(
            key=r"pause",
            value=r"(?P<duration>\d+)"
        )
    )


    class EventListItem(object):
        """
        Representation of an EventListItem (ELI)
        """
        # default values for each main param
        # make sure this matches push/queue
        DEFAULT_VALUES = (
            False, # notify
            None, # context
        )

        ITEM_LEN = len(DEFAULT_VALUES) + 1 # defaults + event label

        IDX_EVENT_LABEL = 0
        IDX_NOTIFY = 1
        IDX_CONTEXT = 2

        def __init__(self, data):
            """
            Constructor

            IN:
                data - the data directly from event list
            """
            self._eli = data

        def __repr__(self):
            return "<{}: (data: {})>".format(
                type(self).__name__,
                self._eli
            )

        @staticmethod
        def build(evl, *args):
            """
            Builds an ELI.

            IN:
                evl - event label
                *args - the other args for an EventListItem.

            RETURNS: EventListItem object
            """
            return EventListItem(EventListItem._build_raw(evl, *args))

        @staticmethod
        def _build_raw(evl, *args):
            """
            Builds raw data for an ELI.

            args are same as EventListItem.build

            RETURNS: raw data
            """
            data = list(
                (evl, ) + args + EventListItem.DEFAULT_VALUES[len(args):]
            )

            # adjust context to be persistntable
            ctx = data[EventListItem.IDX_CONTEXT]
            if isinstance(ctx, store.MASEventContext):
                data[EventListItem.IDX_CONTEXT] = ctx._to_dict()

            return tuple(data)

        def _raw(self):
            """
            Gets the data for this EventListItem that is ready for
            the actual event list.

            RETURNS: raw event list data
            """
            return self._eli

        @property
        def event_label(self):
            """
            Gets the event label from this EventListItem

            Aliases: ev_label, evl

            RETURNS: event label
            """
            return self._eli[self.IDX_EVENT_LABEL]

        # aliases
        eventlabel = event_label # because Event
        ev_label = event_label
        evl = event_label

        @property
        def notify(self):
            """
            Gets the notify value from this EventListItem

            RETURNS: notify
            """
            return self._eli[self.IDX_NOTIFY]

        @property
        def context(self):
            """
            Gets the context from this EventListItem

            Aliases: ctx

            RETURNS: context (MASEventContext object)
            """
            return store.MASEventContext(self._eli[self.IDX_CONTEXT])

        # aliases
        ctx = context


    # as well as special functions
    def addIfNew(items, pool):
        #
        # Adds the list of given items to the given pool (assuemd to be list)
        # such that new only new items are added.
        #
        # IN:
        #   item - list of items to add the given pool
        #   pool - pool to be added to
        #
        # RETURNS:
        #   the pool

        for item in items:
            if item not in pool:
                pool.append(item)
        return pool

    def tuplizeEventLabelList(key_list, db):
        #
        # Creates a list of prompt,label tuple pairs using the given key list
        # and db (dict of events)
        #
        # IN:
        #   key_list - list of keys (labels)
        #   db - dict of events
        #
        # RETURNS:
        #   list of tuples of the following format:
        #       [0]: prompt/caption
        #       [1]: eventlabel
        return [(db[x].prompt, x) for x in key_list]


    def _isFuture(ev, date=None):
        """INTERNAL
        Checks if the start_date of the given event happens after the
        given time.

        IN:
            ev - Event to check the start_time
            date - a datetime object used to check against
                If None is passed it will check against current time
                (Default: None)

        RETURNS:
            True if the Event's start_date is in the future, False otherwise
        """

        # sanity check
        if ev is None:
            return False

        # if no date is passed
        if date is None:
            date = datetime.datetime.now()

        start_date = ev.start_date

        # if we don't have an end date we return false
        if start_date is None:
            return False

        return date < start_date


    def _isPast(ev, date=None):
        """INTERNAL
        Checks if the end_date of the given event happens before the
        given time.

        IN:
            ev - Event to check the start_time
            date - a datetime object used to check against
                If None is passed it will check against current time
                (Default: None)

        RETURNS:
            True if the Event's end_date is in the past, False otherwise
        """

        # if there's no event to check return False
        if ev is None:
            return False

        # if no date is passed
        if date is None:
            date = datetime.datetime.now()

        end_date = ev.end_date

        # if we don't have an end date we return false
        if end_date is None:
            return False

        return end_date < date


    def _isPresent(ev):
        """INTERNAL
        Checks if current date falls within the given event's start/end date
        range

        IN:
            ev - Event to check the start_time and end_time

        RETURNS:
            True if current time is inside the  Event's start_date/end_date
            interval, False otherwise
        """
        # check we have an event
        if ev is None:
            return False

        start_date = ev.start_date
        end_date = ev.end_date

        current = datetime.datetime.now()

        # return false if either start or end is None
        if start_date is None or end_date is None:
            return False

        return start_date <= current <= end_date


    def _hideEvent(
            event,
            lock=False,
            derandom=False,
            depool=False,
            decond=False
        ):
        """
        Internalized hideEvent
        """
        if event:

            if lock:
                event.unlocked = False

            if derandom:
                event.random = False

            if depool:
                event.pool = False

            if decond:
                event.conditional = None


    def _hideEventLabel(
            eventlabel,
            lock=False,
            derandom=False,
            depool=False,
            decond=False,
            eventdb=event_database
        ):
        """
        Internalized hideEventLabel
        """
        ev = eventdb.get(eventlabel, None)

        _hideEvent(
            ev,
            lock=lock,
            derandom=derandom,
            depool=depool,
            decond=decond
        )


    def _lockEvent(ev):
        """
        Internalized lockEvent
        """
        _hideEvent(ev, lock=True)


    def _lockEventLabel(evlabel, eventdb=event_database):
        """
        Internalized lockEventLabel
        """
        _hideEventLabel(evlabel, lock=True, eventdb=eventdb)


    def _unlockEvent(ev):
        """
        Internalized unlockEvent
        """
        if ev:
            ev.unlocked = True


    def _unlockEventLabel(evlabel, eventdb=event_database):
        """
        Internalized unlockEventLabel
        """
        _unlockEvent(eventdb.get(evlabel, None))


    def addYearsetBlacklist(evl, expire_dt):
        """
        Adds the given evl to the yearset blacklist, with the given expiration
        dt

        IN:
            evl - event label
            expire_dt - when the evl should be removed from the blacklist
        """
        if expire_dt > datetime.datetime.now():
            store.persistent._mas_ev_yearset_blacklist[evl] = expire_dt


    def cleanYearsetBlacklist():
        """
        Goes through the year setblacklist and removes expired entries
        """
        now_dt = datetime.datetime.now()
        for evl in tuple(store.persistent._mas_ev_yearset_blacklist.keys()):
            if store.persistent._mas_ev_yearset_blacklist[evl] <= now_dt:
                store.persistent._mas_ev_yearset_blacklist.pop(evl)


    def isYearsetBlacklisted(evl):
        """
        Checks if the given evl is yearset blacklisted. Also checks expiration
        date and removes if needed.

        IN:
            evl - event label

        RETURNS: True if blacklisted, false if not
        """
        if evl not in store.persistent._mas_ev_yearset_blacklist:
            return False

        expire_dt = store.persistent._mas_ev_yearset_blacklist[evl]
        if expire_dt <= datetime.datetime.now():
            store.persistent._mas_ev_yearset_blacklist.pop(evl)
            return False

        return True


init python:
    import store.evhand as evhand
    import datetime


    class MASEventContext(mas_utils.IsolatedFlexProp):
        """
        Context for events. Supports flexible attributes (like persistent).

        However, only picklable primitive datatypes are allowed.
        See mas_ev_data_ver._strict_can_pickle for more info.
        In general, DO NOT USE OBJECTS - they will be denied entry.

        To get the current event context, call MASEventContext.get.
        """
        _this_ev_ctx = None # no one mess with this please i swear

        ## string constants
        __CTX_CTX = "current event: {0}"
        __ERR_NON_PICKLE = (
            "object of type '{0}' cannot be added to context | {1}"
        )
        __ERR_RECUR = (
            "recursion error hit while adding object of type '{0}' to context "
            "| {1}"
        )

        def __init__(self, ctx_data=None):
            """
            Constructor

            IN:
                ctx_data - context data directly from event list. Optional.
                    (Default: None)
            """
            super(MASEventContext, self).__init__()
            if ctx_data is not None:
                self._from_dict(ctx_data)

        def __setattr__(self, name, value):
            """
            We don't allow types that cannot be saved to persistent
            """
            if MASEventContext.is_allowed_data(value):
                super(MASEventContext, self).__setattr__(name, value)

        @classmethod
        def is_allowed_data(cls, thing):
            """
            Checks if the given thing is allowed to be used in context.

            IN:
                thing - thing to check

            RETURNS: True if the thing can be used, False otherwise
            """
            can_pickle, recur_error = store.mas_ev_data_ver._strict_can_pickle(thing)
            if can_pickle:
                return True

            # otherwise - we are going to log this as an error but no crash.
            # we'll give the current ev in the message as ctx if it exists.
            if store.mas_globals.this_ev is None:
                context = ""
            else:
                context = cls.__CTX_CTX.format(
                    store.mas_globals.this_ev.eventlabel
                )

            if recur_error:
                # log recursion error
                store.mas_utils.mas_log.error(cls.__ERR_RECUR.format(
                    type(thing).__name__,
                    context
                ))

            else:
                # log disallowed object
                store.mas_utils.mas_log.error(cls.__ERR_NON_PICKLE.format(
                    type(thing).__name__,
                    context
                ))

        @classmethod
        def get(cls):
            """
            Gets current event context.
            """
            if cls._this_ev_ctx is None:
                cls._this_ev_ctx = cls()

            return cls._this_ev_ctx

        @classmethod
        def _set(cls, eli):
            """
            Sets current event context - only for internal use.

            IN:
                eli - EventListItem object. Use None to clear.
            """
            if eli is None:
                cls._this_ev_ctx = None
            else:
                cls._this_ev_ctx = eli.ctx


    class MASEventList(object):
        """
        representation of persistent.event_list*

        *not literally, this should be considered an abstraction layer with
        unified naming.
        """

        # current event functions

        @staticmethod
        def clear_current():
            """
            Clears the current event aka persistent eli data.
            """
            MASEventList._set_current(None)

        @staticmethod
        def load_current():
            """
            Loads the current event as an EventListItem, which is stored in
            persistent eli data.

            RETURNS: EventListItem of the current event, or None if no current
                event.
            """
            if persistent._mas_curr_eli_data is None:
                return None

            return evhand.EventListItem.build(*persistent._mas_curr_eli_data)

        @staticmethod
        def _set_current(eli):
            """
            Sets the current event aka persistent eli data using the given
            EventListItem object.

            Also sets persistent.current_monikatopic.

            IN:
                eli - the EventListItem object to set as the current one.
                    pass None to clear the current event data.
            """
            if eli is None:
                new_eli_data = None
                new_curr_moni_topic = None
            else:
                new_eli_data = eli._raw()
                new_curr_moni_topic = eli.evl

            persistent._mas_curr_eli_data = new_eli_data
            persistent.current_monikatopic = new_curr_moni_topic

        @staticmethod
        def sync_current():
            """
            Syncs the current event persistent vars, aka:
                - current_monikatopic
                - _mas_curr_eli_data
            """
            curr_eli = MASEventList.load_current()

            if curr_eli is None:

                if renpy.has_label(str(persistent.current_monikatopic)):
                    # to handle unexpected uses, we'll build an eli for this
                    # if this var is set but no eli data was found.
                    MASEventList._set_current(evhand.EventListItem.build(
                        str(persistent.current_monikatopic)
                    ))

                else:
                    MASEventList.clear_current()

            else:
                MASEventList._set_current(curr_eli)

        # event list functions

        @staticmethod
        def clean():
            """
            Cleans the event list and makes sure all events are of the
            appropriate length and have a valid label.
            """
            for index in MASEventList.rev_idx_iter():
                item_raw = persistent.event_list[index]

                # type check
                if not isinstance(item_raw, tuple):
                    # 1st-gen event list (only event labels)
                    new_item = evhand.EventListItem.build(item_raw)

                elif len(item_raw) < evhand.EventListItem.ITEM_LEN:
                    # 2gen+ event list (not enough items)
                    new_item = evhand.EventListItem.build(*item_raw)

                else:
                    # current
                    new_item = evhand.EventListItem(item_raw)

                # label check
                if renpy.has_label(new_item.evl):
                    persistent.event_list[index] = new_item._raw()

                else:
                    persistent.event_list.pop(index)

        @staticmethod
        def iter():
            """
            an iterable over event list that yields EventListITem objects

            ASSUMES event list data is valid

            RETURNS: generator/iterable over persistent.event_list
            """
            for data in persistent.event_list:
                yield evhand.EventListItem(data)

        @staticmethod
        def is_paused():
            """
            Checks if events are paused - also updates the event pause dt vars.

            RETURNS: True if events are paused, False otherwise.
            """
            if mas_globals.event_unpause_dt is None:
                return False

            if datetime.datetime.utcnow() < mas_globals.event_unpause_dt:
                return True

            mas_globals.event_unpause_dt = None
            return False

        @staticmethod
        def _next():
            """
            Gets the next event's data and its location in the event_list.
            This takes event restrictions into account, aka pausing and idle.

            RETURNS: tuple of the following format:
                [0] - EventListItem of the next event, or None if no next event
                [1] - the index of the event, or -1 if no next event
            """
            if len(persistent.event_list) < 1:
                return None, -1

            is_paused = MASEventList.is_paused()

            for index, item in MASEventList.rev_enum_iter():
                ev = mas_getEV(item.evl)

                if (
                        not is_paused
                        or ev is None # allows non-event labels
                        or "skip_pause" in ev.rules
                ):

                    if mas_globals.in_idle_mode:
                        # only allow idle events in idle mode

                        if (
                                (ev is not None and ev.show_in_idle)
                                or item.evl in evhand.IDLE_WHITELIST
                        ):
                            return item, index

                    else:
                        return item, index

            # no valid event available
            return None, -1

        @staticmethod
        def peek():
            """
            Gets the EventListItem for the next event on the event list, but
            does NOT remove it.

            This will respect pausing and other next event restrictions.

            Does NOT set additional vars that pop does - please use pop
            when actually planning to execute an event.

            RETURNS: EventListItem object for the next event, or None if no
            next event.
            """
            return MASEventList._next()[0]

        @staticmethod
        def pop():
            """
            Gets the EventListItem for the next event on the event list and
            removes the event from the event list.

            This will respect pausing and other next event restrictions.

            Also sets:
                persistent.current_monikatopic
                persistent._mas_eli_data

            RETURNS: EventListItem object for the next event
            """
            item, loc = MASEventList._next()

            if item is None:
                return None

            if 0 <= loc < len(persistent.event_list): # just in case
                persistent.event_list.pop(loc)

            MASEventList._set_current(item)

            return item

        @staticmethod
        def push(event_label, skipeval=False, notify=False, context=None):
            """
            Pushes an event to the list - this will make the event trigger
            next unless something else is pushed.

            IN:
                @event_label - a renpy label for the event to be called
                skipmidloopeval - do we want to skip the mid loop eval to
                    prevent other rogue events from interrupting.
                    (Defaults: False)
                notify - True will trigger a notification if appropriate. False
                    will not
                    (Default: False)
                context - set to a MASEventContext object to supply extra
                    context to the event
                    (accessible via MASEventContext.get())
                    (Default: None)
            """
            MASEventList._push_eli(evhand.EventListItem.build(
                event_label,
                notify,
                context
            ))

            if skipeval:
                mas_idle_mailbox.send_skipmidloopeval()

        @staticmethod
        def _push_eli(eli):
            """
            Pushes an EventListItem directly. only for internal use.

            IN:
                eli - EventListItem to push
            """
            persistent.event_list.append(eli._raw())

        @staticmethod
        def queue(event_label, notify=False, context=None):
            """
            Queues an event to the list - this will make the event trigger,
            but not right away unless the list is empty.

            IN:
                @event_label - a renpy label for the event to be called
                notify - True will trigger a notification if appropriate, False
                    will not
                    (Default: False)
                context - set to a MASEventContext object to supply extra
                    context to the event
                    (accessible via MASEventContext.get())
                    (Default: None)
            """
            MASEventList._queue_eli(evhand.EventListItem.build(
                event_label,
                notify,
                context
            ))

        @staticmethod
        def _queue_eli(eli):
            """
            Queues an EventListItem directly, only for internal use.

            IN:
                eli - EventListItem to queue
            """
            persistent.event_list.insert(0, eli._raw())

        @classmethod
        def rev_enum_iter(cls):
            """
            Reverse enumerated iterable for event list.

            ASSUMES persistent.event_list is valid

            RETURNS: reverse enumerated iterable:
                [0] - index
                [1] - EventListItem
            """
            for index in cls.rev_idx_iter():
                yield (index, evhand.EventListItem(persistent.event_list[index]))

        @staticmethod
        def rev_idx_iter():
            """
            Reverse index iterable. If you want index iterable, please use
            enumerate with iter.

            RETURNS: reverse index iterable for event list
            """
            return range(len(persistent.event_list)-1, -1, -1)


    def addEvent(
        event,
        eventdb=None,
        skipCalendar=True,
        restartBlacklist=False,
        markSeen=False,
        code="EVE"
    ):
        """
        Adds an event object to the given eventdb dict
        Properly checksfor label and conditional statements
        This function ensures that a bad item is not added to the database

        NOTE: this MUST be ran after init level 4.

        IN:
            event - the Event object to add to database
            eventdb - The Event databse (dict) we want to add to
                NOTE: DEPRECATED. Use code instead.
                NOTE: this can still be used for custom adds.
                (Default: None)
            skipCalendar - flag that marks wheter or not calendar check should
                be skipped
                (Default: True)

            restartBlacklist - True if this topic should be added to the restart blacklist
                (Default: False)

            markSeen - True if this topic should be `True` in persistent._seen_ever.
                (Default: False)

            code - code of the event database to add to.
                (Default: EVE) - event database
        """
        if eventdb is None:
            eventdb = mas_all_ev_db_map.get(code, None)

        if type(eventdb) is not dict:
            raise EventException("Given db is not of type dict")
        if type(event) is not Event:
            raise EventException("'" + str(event) + "' is not an Event object")
        if not renpy.has_label(event.eventlabel):
            raise EventException("'" + event.eventlabel + "' does NOT exist")
        # if event.conditional is not None:
        #     eval(event.conditional)
        #    try:
        #        if eval(event.conditional, globals()):
        #            pass
        #    except:
        #        raise EventException("Syntax error in conditional statement for event '" + event.eventlabel + "'.")
        # if should not skip calendar check and event has a start_date
        if not skipCalendar and type(event.start_date) is datetime.datetime:
            # add it to the calendar database
            store.mas_calendar.addEvent(event)

        # verify the event's dates
        # NOTE: this covers time travel
        if not store.evhand.isYearsetBlacklisted(event.eventlabel):
            Event._verifyAndSetDatesEV(event)

        # check whether we should add the event in the restart blacklist
        if restartBlacklist:
            evhand.RESTART_BLKLST.append(event.eventlabel)

        if markSeen:
            persistent._seen_ever[event.eventlabel] = True

        # now this event has passsed checks, we can add it to the db
        eventdb.setdefault(event.eventlabel, event)

    @store.mas_utils.deprecated("mas_hideEVL", should_raise=True)
    def hideEventLabel(
            eventlabel,
            lock=False,
            derandom=False,
            depool=False,
            decond=False,
            eventdb=evhand.event_database
        ):
        #
        # NOTE: DEPRECATED
        # hide an event in the given eventdb by Falsing its unlocked,
        # random, and pool properties.
        #
        # IN:
        #   eventlabel - label of the event to hide
        #   lock - True if we want to lock this event, False otherwise
        #       (Default: False)
        #   derandom - True if we want to unrandom this event, False otherwise
        #       (Default: False)
        #   depool - True if we want to unpool this event, False otherwise
        #       (Default: False)
        #   decond - True if we want to remove the conditional, False otherwise
        #       (Default: False)
        #   eventdb - the event database (dict) we want to reference
        #       (DEfault: evhand.event_database)
        mas_hideEventLabel(eventlabel, lock, derandom, depool, decond, eventdb)

    @store.mas_utils.deprecated("mas_hideEvent")
    def hideEvent(
            event,
            lock=False,
            derandom=False,
            depool=False,
            decond=False
        ):
        #
        # NOTE: DEPRECATED
        # hide an event by Falsing its unlocked,
        # random, and pool properties.
        #
        # IN:
        #   event - event object we want to hide
        #   lock - True if we want to lock this event, False otherwise
        #       (Default: False)
        #   derandom - True if we want to unrandom this event, False otherwise
        #       (Default: False)
        #   depool - True if we want to unpool this event, False otherwise
        #       (Default: False)
        #   decond - True if we want to remove the conditional, False
        #       otherwise
        #       (Default: False)
        mas_hideEvent(event, lock, derandom, depool, decond)


    def mas_hideEvent(
            ev,
            lock=False,
            derandom=False,
            depool=False,
            decond=False
        ):
        """
        Hide an event by Falsing its unlocked/random/pool props

        IN:
            ev - event object we want to hide
            lock - True if we want to lock this event, False if not
                (Default: False)
            derandom - True fi we want to unrandom this Event, False if not
                (Default: False)
            depool - True if we want to unpool this event, Flase if not
                (Default: False)
            decond - True if we want to remove the conditional, False if not
                (Default: False)
        """
        evhand._hideEvent(
            ev,
            lock=lock,
            derandom=derandom,
            depool=depool,
            decond=decond
        )


    def mas_hideEventLabel(
            ev_label,
            lock=False,
            derandom=False,
            depool=False,
            decond=False,
            eventdb=evhand.event_database
        ):
        """
        Hide an event label by Falsing its unlocked/random/pool props

        NOTE: use this with custom eventdbs

        IN:
            ev_label - label of the event we wnat to hide
            lock - True if we want to lock this event, False if not
                (Default: False)
            derandom - True fi we want to unrandom this Event, False if not
                (Default: False)
            depool - True if we want to unpool this event, Flase if not
                (Default: False)
            decond - True if we want to remove the conditional, False if not
                (Default: False)
            eventdb - event databsae ev_label is in
                (Default: evhand.event_database)
        """
        evhand._hideEventLabel(
            ev_label,
            lock=lock,
            derandom=derandom,
            depool=depool,
            decond=decond,
            eventdb=eventdb
        )


    def mas_showEvent(
            ev,
            unlock=False,
            _random=False,
            _pool=False
        ):
        """
        Show an event by Truing its unlock/ranomd/pool props

        IN:
            ev - event to show
            unlock - True if we want to unlock this event, False if not
                (Default: False)
            _random - True if we want to random this event, Flase otherwise
                (Default: False)
            _pool - True if we want to pool this event, False otherwise
                (Default: False)
        """
        if ev:
            if unlock:
                ev.unlocked = True

            if _random:
                ev.random = True

            if _pool:
                ev.pool = True


    def mas_showEventLabel(
            ev_label,
            unlock=False,
            _random=False,
            _pool=False,
            eventdb=evhand.event_database
        ):
        """
        Shows an event label, by Truing the unlocked, random, and pool
        properties.

        NOTE: use this for custom event dbs

        IN:
            ev_label - label of event to show
            unlock - True if we want to unlock this event, False if not
                (DEfault: False)
            _random - True if we want to random this event, False if not
                (Default: False)
            _pool - True if we want to pool this event, False if not
                (Default: False)
            eventdb - eventdatabase this label belongs to
                (Default: evhannd.event_database)
        """
        mas_showEvent(eventdb.get(ev_label, None), unlock, _random, _pool)

    @store.mas_utils.deprecated("mas_lockEvent", should_raise=True)
    def lockEvent(ev):
        """
        NOTE: DEPRECATED
        Locks the given event object

        IN:
            ev - the event object to lock
        """
        mas_lockEvent(ev)

    @store.mas_utils.deprecated("mas_lockEventLabel", should_raise=True)
    def lockEventLabel(evlabel, eventdb=evhand.event_database):
        """
        NOTE: DEPRECATED
        Locks the given event label

        IN:
            evlabel - event label of the event to lock
            eventdb - Event database to find this label
        """
        mas_lockEventLabel(evlabel, eventdb)


    def mas_lockEvent(ev):
        """
        Locks the given event object

        IN:
            ev - the event object to lock
        """
        evhand._lockEvent(ev)


    def mas_lockEventLabel(evlabel, eventdb=evhand.event_database):
        """
        Locks the given event label

        IN:
            evlabel - event label of the event to lock
            eventdb - Event database to find this label
        """
        evhand._lockEventLabel(evlabel, eventdb=eventdb)


    @store.mas_utils.deprecated("MASEventList.push")
    def pushEvent(event_label, skipeval=False, notify=False):
        """
        This pushes high priority or time sensitive events onto the top of
        the event list

        IN:
            @event_label - a renpy label for the event to be called
            skipmidloopeval - do we want to skip the mid loop eval to
                prevent other rogue events from interrupting.
                (Defaults: False)
            notify - True will trigger a notification if appropriate. False
                will not
                (Default: False)

        ASSUMES:
            persistent.event_list
        """
        MASEventList.push(event_label, skipeval, notify)


    @store.mas_utils.deprecated("MASEventList.queue")
    def queueEvent(event_label, notify=False):
        """
        This adds low priority or order-sensitive events onto the bottom of
        the event list. This is slow, but rarely called and list should be
        small.

        IN:
            @event_label - a renpy label for the event to be called
            notify - True will trigger a notification if appropriate, False
                will not
                (Default: False)

        ASSUMES:
            persistent.event_list
        """
        MASEventList.queue(event_label, notify)


    @store.mas_utils.deprecated("mas_unlockEvent", should_raise=True)
    def unlockEvent(ev):
        """
        NOTE: DEPRECATED
        Unlocks the given evnet object

        IN:
            ev - the event object to unlock
        """
        mas_unlockEvent(ev)

    @store.mas_utils.deprecated("mas_unlockEventLabel")
    def unlockEventLabel(evlabel, eventdb=evhand.event_database):
        """
        NOTE: DEPRECATED
        Unlocks the given event label

        IN:
            evlabel - event label of the event to lock
            eventdb - Event database to find this label
        """
        mas_unlockEventLabel(evlabel, eventdb)


    def mas_unlockEvent(ev):
        """
        Unlocks the given evnet object

        IN:
            ev - the event object to unlock
        """
        evhand._unlockEvent(ev)


    def mas_unlockEventLabel(evlabel, eventdb=evhand.event_database):
        """
        Unlocks the given event label

        IN:
            evlabel - event label of the event to lock
            eventdb - Event database to find this label
        """
        evhand._unlockEventLabel(evlabel, eventdb=eventdb)


    def isFuture(ev, date=None):
        """
        Checks if the start_date of the given event happens after the
        given time.

        IN:
            ev - Event to check the start_time
            date - a datetime object used to check against
                If None is passed it will check against current time
                (Default: None)

        RETURNS:
            True if the Event's start_date is in the future, False otherwise
        """
        return evhand._isFuture(ev, date=date)


    def isPast(ev, date=None):
        """
        Checks if the end_date of the given event happens before the
        given time.

        IN:
            ev - Event to check the start_time
            date - a datetime object used to check against
                If None is passed it will check against current time
                (Default: None)

        RETURNS:
            True if the Event's end_date is in the past, False otherwise
        """
        return evhand._isPast(ev, date=date)


    def isPresent(ev):
        """
        Checks if current date falls within the given event's start/end date
        range

        IN:
            ev - Event to check the start_time and end_time

        RETURNS:
            True if current time is inside the  Event's start_date/end_date
            interval, False otherwise
        """
        return evhand._isPresent(ev)


    @store.mas_utils.deprecated("MASEventList.pop", should_raise=True)
    def popEvent(remove=True):
        """
        DO NOT USE.

        Use MASEventList.pop instead (not exactly the same)
        """
        pass


    def seen_event(event_label):
        """
        Please use mas_seenEvent, this function hasn't been deprecated
        only because it's used a lot in event conditionals
        and I don't want to update them all
        """
        return mas_seenEvent(event_label)

    def mas_seenEvent(event_label):
        """
        This checks if an event has either been seen or is already in the
        event list.

        IN:
            event_lable = The label for the event to be checked

        ASSUMES:
            persistent.event_list
        """
        return renpy.seen_label(event_label) or mas_inEVL(event_label)


    def mas_findEVL(event_label):
        """
        Finds index of the given event label in the even tlist

        IN:
            event_label - event lable to check

        RETURNS: index of the event in teh even tlist, -1 if not found
        """
        for index, item in enumerate(MASEventList.iter()):
            if item.evl == event_label:
                return index

        return -1


    def mas_inEVL(event_label):
        """
        This checks if an event is in the event list

        IN:
            event_label - event lable to check

        RETURNS: True if in event list, False if not
        """
        return mas_findEVL(event_label) > -1


    def mas_rmEVL(event_label):
        """
        REmoves an event from the event list if it exists

        IN:
            event label to remove
        """
        position = mas_findEVL(event_label)
        if position >= 0:
            persistent.event_list.pop(position)


    def mas_rmallEVL(event_label):
        """
        Removes all events with athe given label

        IN:
            event label to remove
        """
        position = mas_findEVL(event_label)
        while position >= 0:
            mas_rmEVL(event_label)
            position = mas_findEVL(event_label)


    def restartEvent():
        """
        This checks if there is a persistent topic, and if there was push it
        back on the stack with a little comment.
        """
        curr_eli = MASEventList.load_current()

        if curr_eli is None:
            return

        # don't push greetings back on the stack
        if not mas_isRstBlk(curr_eli.evl):
            MASEventList._push_eli(curr_eli)
            MASEventList.push('continue_event', skipeval=True)

        MASEventList.clear_current()


    def mas_isRstBlk(topic_label):
        """
        Checks if the event with the current label is blacklistd from being
        restarted

        IN:
            topic_label - label of the event we are trying to restart
        """
        if not topic_label:
            return True

        if topic_label.startswith("greeting_"):
            return True

        if topic_label.startswith("bye"):
            return True

        if topic_label.startswith("i_greeting"):
            return True

        if topic_label.startswith("ch30_reload"):
            return True

        # check the blacklist
        if topic_label in evhand.RESTART_BLKLST:
            return True

        return False

    def mas_cleanEventList():
        """
        Iterates through the event list and removes items which shouldn't be restarted
        """
        for index, item in MASEventList.rev_enum_iter():
            if mas_isRstBlk(item.evl):
                mas_rmEVL(item.evl)

    def mas_cleanJustSeen(eventlist, db):
        """
        Cleans the given event list of just seen items (withitn the THRESHOLD)
        retunrs not just seen items

        IN:
            eventlist - list of event labels to pick from
            db - database these events are tied to

        RETURNS:
            cleaned list of events (stuff not in the time THREASHOLD)
        """
        import datetime
        now = datetime.datetime.now()
        cleanlist = list()

        for evlabel in eventlist:
            ev = db.get(evlabel, None)

            if ev:
                if ev.last_seen:
                    if now - ev.last_seen >= store.evhand.LAST_SEEN_DELTA:
                        cleanlist.append(evlabel)

                else:
                    cleanlist.append(evlabel)

        return cleanlist


    def mas_cleanJustSeenEV(ev_list):
        """
        Cleans the given event list (of events) of just seen items
        (within the THRESHOLD). Returns not just seen items.
        Basically the same as mas_cleanJustSeen, except for Event object lists

        IN:
            ev_list - list of event objects

        RETURNS:
            cleaned list of events (stuff not in the tiem THRESHOLD)
        """
        import datetime
        now = datetime.datetime.now()
        cleaned_list = list()

        for ev in ev_list:
            if ev.last_seen is not None:
                # this topic has been seen before, must check time
                if now - ev.last_seen >= store.evhand.LAST_SEEN_DELTA:
                    cleaned_list.append(ev)

            else:
                # topic never seen before, its clean!
                cleaned_list.append(ev)

        return cleaned_list


    def mas_unlockPrompt(count=1):
        """
        Unlocks a pool event

        IN:
            count - number of pool events to unlock
                (Default: 1)

        RETURNS:
            True if an event was unlocked. False otherwise
        """
        # get locked pool topics that are not banned from unlocking
        pool_evs = [
            ev
            for ev in evhand.event_database.values()
            if (
                Event._filterEvent(ev, unlocked=False, pool=True)
                and "no_unlock" not in ev.rules
            )
        ]
        u_count = count

        # unlock until we out of available ones or unlock credits
        while len(pool_evs) > 0 and u_count > 0:
            ev_index = renpy.random.randint(0, len(pool_evs)-1)
            ev = pool_evs.pop(ev_index)
            mas_unlockEvent(ev)
            ev.unlock_date = datetime.datetime.now()
            u_count -= 1

        # save remaining to pool unlocks
        if u_count > 0:
            persistent._mas_pool_unlocks += u_count

        # determine return value
        # if these are different, then we unlocked something
        return u_count != count


init 1 python in evhand:
    # mainly to contain action-based functions and fill an appropriate action
    # map
    # all action-based functions are designed for speed, so they don't
    # do any sort of sanity checks
    # NOTE: do NOT use these in dialogue code. These are designed for
    #   internal use only
    import store
    import datetime

    def actionPush(ev, **kwargs):
        """
        Runs Push Event action for the given event

        IN:
            ev - event to push to event stack
        """
        store.pushEvent(ev.eventlabel, notify=True)


    def actionQueue(ev, **kwargs):
        """
        Runs Queue event action for the given event

        IN:
            ev - event to queue to event stack
        """
        store.queueEvent(ev.eventlabel, notify=True)


    def actionUnlock(ev, **kwargs):
        """
        Unlocks an event. Also setse the unlock_date to the given
            unlock time

        IN:
            ev - event to unlock
            unlock_time - time to set unlock_date to
        """
        ev.unlocked = True
        ev.unlock_date = kwargs.get("unlock_time", datetime.datetime.now())


    def actionRandom(ev, **kwargs):
        """
        Randos an event.

        IN:
            ev - event to random
            rebuild_ev - True if we wish to notify idle to rebuild events
        """
        ev.random = True
        if kwargs.get("rebuild_ev", False):
            store.mas_idle_mailbox.send_rebuild_msg()


    def actionPool(ev, **kwargs):
        """
        Pools an event.

        IN:
            ev - event to pool
        """
        ev.pool = True


    # now to setup the action map
    store.Event.ACTION_MAP = {
        store.EV_ACT_UNLOCK: actionUnlock,
        store.EV_ACT_QUEUE: actionQueue,
        store.EV_ACT_PUSH: actionPush,
        store.EV_ACT_RANDOM: actionRandom,
        store.EV_ACT_POOL: actionPool
    }


# This calls the next event in the list. It returns the name of the
# event called or None if the list is empty or the label is invalid
#
label call_next_event:
    python:
        _ev_list_item = MASEventList.pop()

        # Save persistent here in case of a crash
        # to recover data - see restartEvent()
        renpy.save_persistent()

    if _ev_list_item and renpy.has_label(_ev_list_item.evl):
        # TODO: we should have a way to keep track of how many topics/hr
        #   users tend to end up with. without this data we cant really do
        #   too many things based on topic freqeuency.
        #if not seen_event(event_label):
        #    # give whatver the hourly rate is for unseens
        #    $ store.mas_xp._grant_xp(store.mas_xp.xp_rate)

        $ mas_RaiseShield_dlg()

        $ ev = mas_getEV(_ev_list_item.evl)

        if (
            _ev_list_item.notify
            and (ev is None or ("skip alert" not in ev.rules))
        ):
            #Create a new notif
            if renpy.windows:
                $ mas_display_notif(m_name, mas_win_notif_quips, "Topic Alerts")
            else:
                $ mas_display_notif(m_name, mas_other_notif_quips, "Topic Alerts")

        #Also check here and reset the forced idle exp if necessary
        if ev is not None and "keep_idle_exp" not in ev.rules:
            $ mas_moni_idle_disp.unforce_all(skip_dissolve=True)

        # pre-event setup
        $ mas_globals.this_ev = ev
        $ MASEventContext._set(_ev_list_item)

        call expression _ev_list_item.evl from _call_expression

        # post-event cleanup
        $ MASEventList.clear_current()
        $ MASEventContext._set(None)
        $ mas_globals.this_ev = None

        # Handle idle exp
        $ mas_moni_idle_disp.do_after_topic_logic()

        # refetch just in case
        $ ev = mas_getEV(_ev_list_item.evl)

        if ev is not None:

            # if this is a random topic, make sure it's unlocked for prompts
            if (
                    ev.eventlabel in evhand.event_database
                    and ev.random and not ev.unlocked
            ):
                python:
                    ev.unlocked=True
                    ev.unlock_date=datetime.datetime.now()

            # increment shown count
            $ ev.shown_count += 1
            $ ev.last_seen = datetime.datetime.now()

        if _return is not None:
            $ ret_items = _return.split("|")

            if "derandom" in ret_items:
                $ ev.random = False

            if "no_unlock" in ret_items:
                $ ev.unlocked = False
                $ ev.unlock_date = None

            if "unlock" in ret_items:
                $ ev.unlocked = True
                if ev.unlock_date is None:
                    $ ev.unlock_date = ev.last_seen

            if "rebuild_ev" in ret_items:
                $ mas_rebuildEventLists()

            if "idle" in ret_items:
                $ mas_setupIdleMode(brb_label=ev.eventlabel)

            if "love" in ret_items:
                $ mas_ILY()

            if "quit" in ret_items:
                $ persistent.closed_self = True #Monika happily closes herself
                $ mas_clearNotifs()
                jump _quit

            # Force idle exp
            if "idle_exp" in _return:
                python:
                    _match = re.search(evhand.RET_KEY_PATTERN_IDLE_EXP, _return)
                    if _match is not None:
                        if _match.group("exp") is not None and _match.group("duration") is not None:
                            mas_moni_idle_disp.force_by_code(
                                _match.group("exp"),
                                duration=int(_match.group("duration"))
                            )

                        elif _match.group("tag") is not None:
                            _exp = MASMoniIdleExp.weighted_choice(
                                MASMoniIdleExp.exp_tags_map.get(
                                    _match.group("tag"),
                                    tuple()
                                )
                            )
                            if _exp is not None:
                                mas_moni_idle_disp.force(_exp)

            # Set a pause if needed
            if "pause" in _return:
                python:
                    _match = re.search(evhand.RET_KEY_PATTERN_PAUSE, _return)
                    if _match is not None and _match.group("duration") is not None:
                        mas_setEventPause(int(_match.group("duration")))

            if "prompt" in ret_items:
                show monika idle
                jump prompt_menu

        # loop over until all events have been called
        if len(persistent.event_list) > 0:
            jump call_next_event

    if store.mas_globals.in_idle_mode:
        # idle mode should transition shields
        $ mas_dlgToIdleShield()

    else:
        $ mas_DropShield_dlg()

    # return to normal pose
    if not renpy.showing("monika idle"):
        show monika idle at t11 zorder MAS_MONIKA_Z with dissolve_monika

    return False

#The prompt menu is what pops up when hitting the "Talk" button, it shows a list
#of options for talking to Monika, including the ability to ask her questions
#pulled from a random set of prompts.

label prompt_menu:

    $ mas_RaiseShield_dlg()

    if store.mas_globals.in_idle_mode:
        # if talk is hit here, then we retrieve label from mailbox and
        # call it.
        # after the event is over, we drop shields return to idle flow
        $ cb_label = mas_idle_mailbox.get_idle_cb()

        # NOTE: we call the label directly instead of pushing to event stack
        #   so that if the user quits during the event, we get the appropriate
        #   greeting instead of the regular reload greeting.
        #
        #   This also prevents the end-of-idle label from being saved and
        #   restored on a relaunch, which would make no sense lol.

        # Only call the label if it exists
        if cb_label is not None and renpy.has_label(cb_label):
            call expression cb_label

        # Otherwise reset rv
        else:
            $ _return = None

        # If we want to resume idle mode, we don't reset
        if _return != "idle":
            $ mas_resetIdleMode()
            # NOTE: Clear this here because closing during idle
            # or idle callback could launch a specific greeting
            $ persistent._mas_greeting_type = None

        # Otherwise we have to send the callback label again
        elif cb_label is not None:
            $ mas_idle_mailbox.send_idle_cb(cb_label)

        #Show idle exp here so we dissolve like other topics
        if not renpy.showing("monika idle"):
            show monika idle at t11 zorder MAS_MONIKA_Z with dissolve_monika

        # NOTE: we only need to enable music hotkey since we are in dlg mode
        #$ mas_DropShield_idle()
        $ store.mas_hotkeys.music_enabled = True

        jump prompt_menu_end

    python:
        #We want to adjust the time of day vars
        mas_setTODVars()

        unlocked_events = Event.filterEvents(
            evhand.event_database,
            unlocked=True,
            aff=mas_curr_affection
        )
        sorted_event_labels = Event.getSortedKeys(unlocked_events,include_none=True)

        # we exclude 'mas_show_unseen' from the unseen list since it's only unlocked when the unseen menu is hidden
        # having it added to the unseen list just messes up the counter in the 'mas_show_unseen' prompt
        unseen_event_labels = [
            ev_label
            for ev_label in sorted_event_labels
            if not seen_event(ev_label) and ev_label != "mas_show_unseen"
        ]

        if len(unseen_event_labels) > 0 and persistent._mas_unsee_unseen:
            mas_showEVL('mas_show_unseen','EVE',unlock=True)
            unseen_num = len(unseen_event_labels)
            mas_setEVLPropValues(
                "mas_show_unseen",
                prompt="I would like to see 'Unseen' ([unseen_num]) again"
            )
        else:
            mas_hideEVL('mas_show_unseen','EVE',lock=True)

        repeatable_events = Event.filterEvents(
            evhand.event_database,
            unlocked=True,
            pool=False,
            aff=mas_curr_affection
        )

    #Top level menu
    # NOTE: should we force this to a particualr exp considering that
    # monika now rotates
    # NOTE: actually we could use boredom setup in here.
    show monika at t21
    #To make the menu line up right we have to build it up manually
    python:
        talk_menu = []
        if len(unseen_event_labels)>0 and not persistent._mas_unsee_unseen:
            # show unseen if we have unseen events and the player hasn't chosen to hide it
            talk_menu.append((_("{b}Unseen{/b}"), "unseen"))
        if mas_hasBookmarks():
            talk_menu.append((_("Bookmarks"),"bookmarks"))
        talk_menu.append((_("Hey, [m_name]..."), "prompt"))
        if len(repeatable_events)>0:
            talk_menu.append((_("Repeat conversation"), "repeat"))
        if _mas_getAffection() > -50:
            if mas_passedILY(pass_time=datetime.timedelta(0,10)):
                talk_menu.append((_("I love you too!"),"love_too"))
            else:
                talk_menu.append((_("I love you!"), "love"))
        talk_menu.append((_("I feel..."), "moods"))
        talk_menu.append((_("Goodbye"), "goodbye"))
        talk_menu.append((_("Nevermind"),"nevermind"))

        renpy.say(m, store.mas_affection.talk_quip()[1], interact=False)
        madechoice = renpy.display_menu(talk_menu, screen="talk_choice")

    if madechoice == "unseen":
        call show_prompt_list(unseen_event_labels)

    elif madechoice == "bookmarks":
        call mas_bookmarks

    elif madechoice == "prompt":
        call prompts_categories(True)

    elif madechoice == "repeat":
        call prompts_categories(False)

    elif madechoice == "love":
        $ pushEvent("monika_love", skipeval=True)
        $ _return = True

    elif madechoice == "love_too":
        $ pushEvent("monika_love_too", skipeval=True)
        $ _return = True

    elif madechoice == "moods":
        call mas_mood_start

    elif madechoice == "goodbye":
        call mas_farewell_start

    else: #nevermind
        $ _return = None

    # check explicitly for False here due to how farewells return
    if _return is False:
        jump prompt_menu

label prompt_menu_end:
    show monika at t11
    if store.mas_globals.in_idle_mode:
        $ mas_dlgToIdleShield()
    else:
        $ mas_DropShield_dlg()
    jump ch30_visual_skip

label show_prompt_list(sorted_event_labels):
    $ import store.evhand as evhand

    #Get list of unlocked prompts, sorted by unlock date
    python:
        prompt_menu_items = [
            (mas_getEVLPropValue(ev_label, "prompt"), ev_label, False, False)
            for ev_label in sorted_event_labels
        ]

        hide_unseen_event = mas_getEV("mas_hide_unseen")

        final_items = (
            (_("I don't want to see this menu anymore"), "mas_hide_unseen", False, False, 20),
            (_("Nevermind"), False, False, False, 0)
        )

    call screen mas_gen_scrollable_menu(prompt_menu_items, mas_ui.SCROLLABLE_MENU_LOW_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, *final_items)

    if _return:
        $ mas_setEventPause(None)
        $ pushEvent(_return, skipeval=True)

    return _return

label prompts_categories(pool=True):

    # this acts as a stack for category lists
    # each item is an _NT_CAT_PANE namedtuple
    $ cat_lists = list()

    $ current_category = list()
    $ import store.evhand as evhand
    $picked_event = False
    python:

        # get list of unlocked events for the master category list
        unlocked_events = Event.filterEvents(
            evhand.event_database,
#            full_copy=True,
#                category=[False,current_category],
            unlocked=True,
            pool=pool,
            aff=mas_curr_affection,
            flag_ban=EV_FLAG_HFM
        )

        # add all categories the master category list
        main_cat_list = list()
        no_cat_list = list() # contain events with no categories
        for key in unlocked_events:
            if unlocked_events[key].category:
                evhand.addIfNew(unlocked_events[key].category, main_cat_list)
            else:
                no_cat_list.append(unlocked_events[key])

        # sort the lists
        main_cat_list.sort()
        no_cat_list.sort(key=Event.getSortPrompt)

        # tuplelize the main the category list
        # NOTE: we use a 2nd list here to do displaying, keeping track of the
        # older cat list for checking if a category was picked
        dis_cat_list = [(x.capitalize() + "...",x) for x in main_cat_list]

        # tupelize the event list
#        no_cat_list = evhand.tuplizeEventLabelList(no_cat_list, unlocked_events)
        no_cat_list = [(x.prompt, x.eventlabel) for x in no_cat_list]

        # extend the display cat list with no category items
        dis_cat_list.extend(no_cat_list)

        # push that master list into the category_lists
        cat_lists.append(evhand._NT_CAT_PANE(dis_cat_list, main_cat_list))

    while not picked_event:
        python:
            prev_items, prev_cats = cat_lists[len(cat_lists)-1]

            # in this case, we only want to display the root category list
            if len(current_category) == 0:
                main_items = None

            else:

                # in this case, we have to generate the next menu
                # current_category contains the selected categories, so we
                # need to search using those categories

                # get list of unlocked events
                unlocked_events = Event.filterEvents(
                    evhand.event_database,
#                    full_copy=True,
                    category=(False,current_category),
                    unlocked=True,
                    pool=pool,
                    aff=mas_curr_affection,
                    flag_ban=EV_FLAG_HFM
                )

                # add deeper categories to a list
                # NOTE: not implemented because we dont have subfolders atm.
                #   maybe one day, but we would need a structure to link
                #   main categories to subcats

                # otherwise make sort event list
                no_cat_list = sorted(
                    unlocked_events.values(),
                    key=Event.getSortPrompt
                )

                # but remake into display
                no_cat_list = [(x.prompt, x.eventlabel) for x in no_cat_list]

                # NOTE: if we have subcategories, then we need to make a main
                # pane

                # no cateogries here
                main_cats = []

                # setup items
                main_items = no_cat_list

                """ KEEP this for legacy purposes
#            sorted_event_keys = Event.getSortedKeys(unlocked_events,include_none=True)

            prompt_category_menu = []
            #Make a list of categories

            #Make a list of all categories
            subcategories=set([])
            for event in sorted_event_keys:
                if unlocked_events[event].category is not None:
                    new_categories=set(unlocked_events[event].category).difference(set(current_category))
                    subcategories=subcategories.union(new_categories)

            subcategories = list(subcategories)
            for category in sorted(subcategories, key=lambda s: s.lower()):
                #Don't list additional subcategories if adding them wouldn't change the same you are looking at
                test_unlock = Event.filterEvents(evhand.event_database,full_copy=True,category=[False,current_category+[category]],unlocked=True)

                if len(test_unlock) != len(sorted_event_keys):
                    prompt_category_menu.append([category.capitalize() + "...",category])


            #If we do have a category picked, make a list of the keys
            if sorted_event_keys is not None:
                for event in sorted_event_keys:
                    prompt_category_menu.append([unlocked_events[event].prompt,event])
                """

        call screen twopane_scrollable_menu(prev_items, main_items, evhand.LEFT_AREA, evhand.LEFT_XALIGN, evhand.RIGHT_AREA, evhand.RIGHT_XALIGN, len(current_category)) nopredict



        if _return in prev_cats:
            # we selected a category from teh previous pane
            python:
                if len(current_category) > 0:
                    current_category.pop()
                current_category.append(_return)

# TODO: if we have subcategories, this needs to be setup properly
#        elif _return in main_cats:
            # we selected a category in the main pane
#            $ current_category.append(_return)
#            $ cat_lists.append(main_pane)
#            $ is_root = False

#        elif _return == -2: # Thats enough for now
#            $picked_event = True

        elif _return == -1: # go back
            if len(current_category) > 0:
                $ current_category.pop()

        else: # event picked
            $ picked_event = True
            #So we don't push garbage
            if _return is not False:
                $ mas_setEventPause(None)
                $ pushEvent(_return, skipeval=True)

    return _return

# sets up the bookmarks menu
init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="mas_bookmarks",unlocked=False,rules={"no_unlock":None}))
    # NOTE: do not use this as an ev.

label mas_bookmarks:
    show monika idle
    python:
        #Map for label prefixes: label_suffix_get_function
        #NOTE: The function MUST take in the event object as a parameter
        prompt_suffix_map = {
            "mas_song_": store.mas_songs.getPromptSuffix
        }

        # generate list of propmt/label tuples of bookmarks
        bookmarks_items = []
        for ev in mas_get_player_bookmarks(persistent._mas_player_bookmarked):
            # only if it is not flagged to be hidden
            if Event._filterEvent(ev, flag_ban=EV_FLAG_HFM):
                label_prefix = mas_bookmarks_derand.getLabelPrefix(ev.eventlabel)

                #Get the suffix function
                suffix_func = prompt_suffix_map.get(label_prefix)

                #Now call it if it exists to get the suffix
                prompt_suffix = suffix_func(ev) if suffix_func else ""

                #Now append based on the delegate
                bookmarks_items.append(
                    (renpy.substitute(ev.prompt + prompt_suffix), ev.eventlabel, False, False)
                )

        bookmarks_items.sort()

        bk_menu_final_items = (
            (_("I'd like to remove a bookmark"), "remove_bookmark", False, False, 20),
            (_("Nevermind"), "nevermind", False, False, 0)
        )

    # FALL THROUGH

label mas_bookmarks_loop:
    if not bookmarks_items:
        show monika idle
        return True

    show monika at t21
    call screen mas_gen_scrollable_menu(bookmarks_items, mas_ui.SCROLLABLE_MENU_LOW_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, *bk_menu_final_items)

    $ topic_choice = _return

    if topic_choice == "nevermind":
        # nevermind was selected
        return False

    elif topic_choice == "remove_bookmark":
        # prompt for bookmarks to remove
        call mas_bookmarks_unbookmark(bookmarks_items)
        show monika idle
        # the list might have been regenerated
        $ bookmarks_items = _return

    else:
        # got label, let's push
        show monika at t11
        $ mas_setEventPause(None)
        $ pushEvent(topic_choice, skipeval=True)
        return True

    jump mas_bookmarks_loop

# unbookmark flow
# Removes bookmarks from _mas_player_bookmarked
#
# IN:
#   bookmarks_items - list of displayable menu bookmarks
#
# RETURNS:
#   list of displayable menu bookmarks. migtht be regenerated.
label mas_bookmarks_unbookmark(bookmarks_items):
    python:
        def _convert_items(items, convert_into):
            """
            A local func to convert items from
            gen scrollable menu format into check scrollable one
            and vice versa

            IN:
                items - list of items to convert
                convert_into - type of conversion
                    either "CHECK_ITEMS"
                    or "GEN_ITEMS"

            OUT:
                list of converted items
            """
            if convert_into == "CHECK_ITEMS":
                new_items = []

                for item in items:
                    prompt = item[0]
                    # italic
                    if item[2]:
                        prompt = "{0}{1}{2}".format("{i}", prompt, "{/i}")

                    # bold
                    if item[3]:
                        prompt = "{0}{1}{2}".format("{b}", prompt, "{/b}")

                    new_items.append(
                        (prompt, item[1], False, True, False)
                    )

            else:
                new_items = [
                    (item[0], item[1], False, False)
                    for item in items
                ]

            return new_items

        bookmarks_items = _convert_items(bookmarks_items, "CHECK_ITEMS")

    show monika 1eua at t21

    # decicde which prompt
    if len(bookmarks_items) > 1:
        $ renpy.say(m, "Which bookmarks do you want to remove?", interact=False)

    else:
        $ renpy.say(m, "Just select the bookmark if you're sure you want to remove it.", interact=False)

    call screen mas_check_scrollable_menu(bookmarks_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, selected_button_prompt="Remove selected")

    $ bookmarks_to_remove = _return
    $ bookmarks_items = _convert_items(bookmarks_items, "GEN_ITEMS")

    # sanity check that the user selected something
    if bookmarks_to_remove:
        python:
            for ev_label in bookmarks_to_remove.keys():
                # remove the bookmark from persist (if in it)
                if ev_label in persistent._mas_player_bookmarked:
                    persistent._mas_player_bookmarked.remove(ev_label)

            # filter the removed items to show the menu again
            bookmarks_items = filter(lambda item: item[1] not in bookmarks_to_remove, bookmarks_items)

        show monika at t11
        m 1dsa "Okay, [player].{w=0.2}.{w=0.2}.{w=0.2}{nw}"
        m 3hua "All done!"

    return bookmarks_items
