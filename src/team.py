class Team:
    def __init__(self, name, elo):
        self.name = name
        self.elo = elo

    def __str__(self):
        return f"{self.name} ({self.elo})"