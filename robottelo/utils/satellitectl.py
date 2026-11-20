class SatellitectlCommand:
    """Build a satellitectl command from a subcommand and options."""

    def __init__(self, subcommand, **options):
        self.subcommand = subcommand
        self.options = options

    def get_command(self):
        command = ['satellitectl', self.subcommand]
        for name, value in self.options.items():
            command.extend((f'--{name.replace("_", "-")}', str(value)))
        return ' '.join(command)
