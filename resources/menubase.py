"""Class definitions for a basic menu system for the PiRadio."""


class RadioMenuBase(object):
    """Base class definition.

       This should not be used on its own but is instead subclassed by specific
       menu object definition."""

    def __init__(self, name, items=None):
        """Initialise object.

           Each menu item must define a "name" as this is the text that will
           be displayed by the menu.

           The constructor can also pass an item or add this separately via the
           add_item method.
        """
        self.name = name
        self.items = items or []
        self.menu = self
        self.root = self
        self.idx = 0
        self.parent = None

    def add_item(self, item):
        """Add an item to the current menu.

           Can add menu items or submenus.
        """
        self.items.append(item)

        # We need to keep track of the menu parent so we're able to move up a
        # level as necessary
        if item.parent != self:
            item.parent = self
        if self.parent:
            item.root = self.parent.root
        else:
            item.root = self

    def remove_item(self, item):
        """Removes item from the menu."""
        self.items.remove(item)
        if item.parent == self:
            item.parent = None

    def __repr__(self):
        return "RadioMenu {}".format(self.name)


class RadioMenu(RadioMenuBase):
    """This is the main Radio Menu definition. There should only be one instance
       of this menu.

       This object contains the controls for navigating the menu.
    """
    def __init__(self, name, items=None, modeselect=None, cb_display=None):

        # Callback action when a specific mode is called
        self.modeselect = modeselect

        # Callback function for the LCD display
        self.cb_display = cb_display

        # Initialise the base class
        super(RadioMenu, self).__init__(name, items)

    def draw(self):
        """Updates the display with the current menu item."""
        if self.cb_display:
            self.cb_display(self.menu.items[self.idx].name)

    def up(self):
        """Navigate up the menu."""
        self.idx = (self.idx + 1) % len(self.menu.items)
        self.draw()

    def down(self):
        """Navigate down the menu."""
        self.idx = (self.idx - 1) % len(self.menu.items)
        self.draw()

    def rotate(self, direction):
        """Method to translate signals from the rotary encoder into directions
           for the menu.
        """
        if direction > 0:
            self.up()
        else:
            self.down()

    def select(self, level=None):
        """Method to handle actions when button is pressed on menu item."""

        # If this is a top-level mode item...
        if isinstance(self.menu.items[self.idx], RadioMenuMode):

            # Tell the radio to change mode
            self.modeselect(self.menu.items[self.idx].mode)

            # Change the active menu to the menu for the selected mode.
            self.menu = self.menu.items[self.idx]

            # Reset the index
            self.idx = 0
            self.draw()

        # If it's a submenu
        elif isinstance(self.menu.items[self.idx], RadioSubmenu):

            # Change the active menu to the submenu
            self.menu = self.menu.items[self.idx]

            # Reset the index
            self.idx = 0
            self.draw()

        # If we're here then we've got and end item
        else:

            # Call whatever function is bound to the menu item
            self.menu.items[self.idx].target()

    def set_root(self, menu=None):
        """Sets root definition recursively for menu items."""
        if menu is None:
            menu = self

        for i in menu.items:
            if isinstance(i, RadioSubmenu):
                i.root = self
                self.set_root(i)


class RadioSubmenu(RadioMenuBase):
    """Submenu definition.

       Submenus need to be able to access parent.
    """
    def add_back_item(self):
        """Adds a menu item which navigates user to parent menu."""
        self.add_item(RadioMenuItem("Back", target=self.up_level))

    def up_level(self):
        """Changes the active menu to the parent menu."""
        if self.menu.parent is not None:
            self.root.menu = self.menu.parent
            self.root.idx = 0


class RadioTempMenu(RadioMenuBase):
    """Temporary submenu.

       Should be used to create dynamic menus which can be removed from parent.
    """
    def __init__(self, name, items=None, autodelete=True):
        super(RadioTempMenu, self).__init__(name, items=items)
        self.autodelete = autodelete

    def remove_menu(self):
        if self.parent is not None:
            self.root.menu = self.parent
            self.root.idx = 0


class RadioTempItem(object):
    """Menu item class for callable items."""
    def __init__(self, name, target=None):
        """Initialise a menu item with a specific callback."""
        self.name = name
        self.parent = None
        self._target_func = target

    def target(self):
        self._target_func()
        self.parent.remove_menu()

class RadioMenuMode(RadioSubmenu):
    """Mode menu object.

       Each specific radio mode uses this class as a top-level menu class."""
    def __init__(self, mode):
        """The menu stores a reference to the specific mode so it can be
           activated by the radio.
        """
        self.mode = mode
        super(RadioMenuMode, self).__init__(self.mode.name)


class RadioMenuItem(object):
    """Menu item class for callable items."""
    def __init__(self, name, target=None):
        """Initialise a menu item with a specific callback."""
        self.name = name
        self.parent = None
        self.target = target
