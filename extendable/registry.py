# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)


class ExtendableRegistriesDatabase(dict):
    """Holds an extendable classses registry for each database"""


_extendable_registries_database = ExtendableRegistriesDatabase()
