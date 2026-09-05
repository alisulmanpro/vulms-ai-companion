import asyncio
from app.core.security import CryptographicVault
from prisma import Prisma
from prisma.enums import Role

vault = CryptographicVault()


async def main():
    db = Prisma()
    await db.connect()

    # User 1: Ali Sulman
    await db.user.create(
        data={
            "name": "Ali Sulman",
            "email": "ali.sulman@example.com",
            "emailVerified": True,
            "role": Role.STUDENT,
            "whatsappNumber": "+923279742264",
            "vulmsAccounts": {
                "create": {
                    "studentId": "bc240431077",
                    "encryptedPassword": vault.encrypt("!r!3[qP::rwe2"),
                    "aspSessionId": "",
                    "isActive": False,
                }
            },
        }
    )

    # User 2: Mohsin Raza
    # await db.user.create(
    #     data={
    #         "name": "Mohsin Raza",
    #         "email": "mohsin.raza@example.com",
    #         "emailVerified": True,
    #         "role": Role.STUDENT,
    #         "whatsappNumber": "+923494052473",
    #         "vulmsAccounts": {
    #             "create": {
    #                 "studentId": "bc260220874",
    #                 "encryptedPassword": "Asdf12345!",
    #                 "aspSessionId": "asp_session_mohsin_456",
    #                 "isActive": True,
    #             }
    #         },
    #     }
    # )


    print("Dummy data successfully inserted into Neon PostgreSQL!")
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
