# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# disable undefined variable error, which erroneously triggers
# on forward declarations of classes in lambdas
# pylint: disable=E0602

import graphene

from odoo.addons.graphql_base import OdooObjectType


class Country(OdooObjectType):
    code = graphene.String(required=True)
    name = graphene.String(required=True)


class Partner(OdooObjectType):
    name = graphene.String(required=True)
    street = graphene.String()
    street2 = graphene.String()
    city = graphene.String()
    zip = graphene.String()
    country = graphene.Field(Country)
    email = graphene.String()
    phone = graphene.String()
    is_company = graphene.Boolean(required=True)
    contacts = graphene.List(graphene.NonNull(lambda: Partner), required=True)

    def resolve_country(self, info):
        return self.country_id or None

    def resolve_contacts(self, info):
        return self.child_ids


class Query(graphene.ObjectType):
    all_partners = graphene.List(
        graphene.NonNull(Partner),
        required=True,
        companies_only=graphene.Boolean(),
    )

    reverse = graphene.String(
        required=True,
        description="Reverse a string",
        word=graphene.String(required=True),
    )

    def resolve_all_partners(self, info, companies_only=False):
        domain = []
        if companies_only:
            domain.append(("is_company", "=", True))
        return info.context["env"]["res.partner"].search(domain)

    def resolve_reverse(self, info, word):
        return word[::-1]


schema = graphene.Schema(query=Query)
