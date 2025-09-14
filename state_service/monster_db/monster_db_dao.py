import os

import psycopg2

from pod_of_tokyo_commons.constants import OUTSIDE_KEY

TABLE_NAME = "MonsterStateStore"


class MonsterDbDao:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
        )
        self.cursor = self.connection.cursor()
        self.player_id = os.environ["PLAYER_ID"]
        self.monster_name = os.environ["MONSTER_NAME"]
        self.create_table()
        self.create_monster()

    def create_table(self):
        self.cursor.execute(
            f"""
        CREATE TABLE IF NOT EXISTS "{TABLE_NAME}"(
            id SERIAL PRIMARY KEY,
            player_id INT,
            name TEXT NOT NULL,
            health INT,
            score INT,
            energy INT,
            location TEXT
        );
        """
        )
        self.connection.commit()

    def create_monster(self):
        self.cursor.execute(
            f"""
        SELECT COUNT(*) FROM "{TABLE_NAME}" WHERE player_id = %s
        """,
            (self.player_id),
        )
        count = self.cursor.fetchone()[0]
        if count > 0:
            return

        self.cursor.execute(
            f"""
        INSERT INTO "{TABLE_NAME}" (player_id, name, health, score, energy, location)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (self.player_id, self.monster_name, 10, 0, 0, OUTSIDE_KEY),
        )
        self.connection.commit()

    def decrease_health(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET health = health - %s
        WHERE player_id = %s
        """,
            (amount, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("health")

    def increase_health(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET health = health + %s
        WHERE player_id = %s
        """,
            (amount, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("health")

    def increase_score(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET score = score + %s
        WHERE player_id = %s
        """,
            (amount, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("score")

    def decrease_score(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET score = score - %s
        WHERE player_id = %s
        """,
            (amount, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("score")

    def increase_energy(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET energy = energy + %s
        WHERE player_id = %s
        """,
            (amount, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("energy")

    def decrease_energy(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET energy = energy - %s
        WHERE player_id = %s
        """,
            (amount, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("energy")

    def update_location(self, location):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET location = %s
        WHERE player_id = %s
        """,
            (location, self.player_id),
        )
        self.connection.commit()
        return self.get_attribute("location")

    def get_attribute(self, attribute):
        self.cursor.execute(
            f"""
        SELECT {attribute} FROM "{TABLE_NAME}" WHERE player_id = %s
        """,
            (self.player_id),
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_stats(self):
        self.cursor.execute(
            f"""
        SELECT name, health, score, energy, location FROM "{TABLE_NAME}" WHERE player_id = %s
        """,
            (self.player_id),
        )
        result = self.cursor.fetchone()
        return {
            "name": result[0],
            "health": result[1],
            "score": result[2],
            "energy": result[3],
            "location": result[4],
        }
