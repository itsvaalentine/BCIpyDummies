class ActionMapper:

    def map(self, action, power):
        if action == "left" and power >= 0.8:
            return "A"
        if action == "right":
            return "D"
        if action == "lift":
            return "SPACE"
        return None
