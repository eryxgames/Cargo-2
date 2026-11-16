"""The Hauler Hansa: dues every ten turns, bonds that lower them."""

class HansaMixin:
    """The Game's dealings with the Hansa. Game inherits it (game/world.py)."""
    # The Hansa runs the convoys between stars. Every ten turns it charges convoy dues, and the
    # dues grow; Hansa bonds lower them. Unpaid dues gather a surcharge and the convoy master
    # takes cargo for them.
    DUES_EVERY = 10

    def dues(self):
        periods = self.turn // self.DUES_EVERY
        hike = getattr(self, "dues_hike", 1.0) if self.turn <= getattr(self, "dues_hike_until", 0) else 1.0
        due = 600 * periods ** 1.35 * hike
        return int(due * 0.88 ** getattr(self, "hansa_bonds", 0))

    def bond_price(self):
        return int(4000 * 1.15 ** getattr(self, "hansa_bonds", 0))

    def collect_dues(self):
        ship = self.ship
        due = self.dues() + getattr(self, "dues_arrears", 0)
        paid = min(due, max(0, int(ship.money)))
        ship.money -= paid
        owed = due - paid
        lines = ["Hansa convoy dues: %s." % self.format_money(due)]
        if owed <= 0:
            self.dues_arrears = 0
            lines.append("Paid. The convoy master stamps your berth card.")
            color = '33'
        else:
            owed = int(owed * 1.1)
            lines.append("You could pay %s. %s stays on the books, with a ten per cent surcharge." % (
                self.format_money(paid), self.format_money(owed)))
            # the convoy master takes cargo for what is owed
            for good in ('tech', 'agri', 'salt', 'fuel'):
                if owed <= 0 or ship.cargo[good] <= 0:
                    continue
                price = max(1, self.current_location.market.get(good, 0) or 20)
                taken = min(ship.cargo[good], int(owed / price) + 1)
                ship.cargo[good] -= taken
                owed -= int(taken * price)
                lines.append("The convoy master takes %d %s against the debt." % (taken, good))
            self.dues_arrears = max(0, owed)
            ship.passenger_reputation -= 3
            lines.append("Word gets round: reputation -3.")
            color = '31'
        lines.append("Next dues in %d turns: about %s. Bonds lower them (hansa/ha)." % (
            self.DUES_EVERY, self.format_money(self.dues_at(self.turn + self.DUES_EVERY))))
        self.display_simple_message([line for text in lines for line in self.word_wrap(text)], 3, color=color)

    def dues_at(self, turn):
        now = self.turn
        self.turn = turn
        try:
            return self.dues()
        finally:
            self.turn = now

    def buy_bonds(self, count=1, announce=True):
        bought = 0
        for _ in range(count):
            price = self.bond_price()
            if self.ship.money < price:
                break
            self.ship.money -= price
            self.hansa_bonds = getattr(self, "hansa_bonds", 0) + 1
            self.bonds_paid = getattr(self, "bonds_paid", 0) + price
            bought += 1
        if announce and bought:
            self.display_simple_message("Bought %d Hansa bond%s. You hold %d; dues are %d%% lower." % (
                bought, "" if bought == 1 else "s", self.hansa_bonds, round(100 * (1 - 0.88 ** self.hansa_bonds))))
        return bought

    def sell_bonds(self):
        """Cash the bonds in at what they cost (the Hansa buys back at face value)."""
        held = getattr(self, "hansa_bonds", 0)
        value = getattr(self, "bonds_paid", 0)
        self.hansa_bonds, self.bonds_paid = 0, 0
        self.ship.money += value
        return held, value

    def handle_hansa(self):
        """The Hansa terminal: dues, bonds, and the convoy office's price board."""
        while True:
            bonds = getattr(self, "hansa_bonds", 0)
            next_turn = (self.turn // self.DUES_EVERY + 1) * self.DUES_EVERY
            rows = [["Hansa terminal - " + self.current_location.name], [""]]
            for text in (
                    "The Hansa runs the convoys between the stars. Every %d turns it charges convoy dues, "
                    "and the dues go up as the routes get busier." % self.DUES_EVERY,
                    "Next dues at turn %d: %s.%s" % (next_turn, self.format_money(self.dues_at(next_turn)),
                                                     (" Owed from before: %s." % self.format_money(self.dues_arrears))
                                                     if getattr(self, "dues_arrears", 0) else ""),
                    "Bonds held: %d (dues %d%% lower). The next bond costs %s and takes another 12%% off." % (
                        bonds, round(100 * (1 - 0.88 ** bonds)), self.format_money(self.bond_price()))):
                rows.extend([line] for line in self.word_wrap(text))
                rows.append([""])
            rows.extend([["bond/b: buy a bond"], ["prices/p: the convoy office's price board"],
                         ["pay/pd: pay what you owe now"]])
            print(self.create_box(rows, 'double'))
            action = self.validate_input("Hansa - choose (Enter to leave): ", ['bond', 'b', 'prices', 'p', 'pay', 'pd'])
            if action is None:
                return
            if action in ('bond', 'b'):
                if not self.buy_bonds(1):
                    self.display_simple_message("Not enough money for a bond (%s)." % self.format_money(self.bond_price()))
            elif action in ('prices', 'p'):
                self.show_forecast("The convoy office's price board")
            elif action in ('pay', 'pd'):
                owed = getattr(self, "dues_arrears", 0)
                paid = min(owed, int(self.ship.money))
                self.ship.money -= paid
                self.dues_arrears = owed - paid
                self.display_simple_message("Paid %s. Still owed: %s." % (
                    self.format_money(paid), self.format_money(self.dues_arrears)))
