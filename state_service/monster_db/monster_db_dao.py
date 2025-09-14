import os

import psycopg2

TABLE_NAME = "MonsterStateStore"

TOKYO_CITY_KEY = "tokyo-city"
TOKYO_BAY_KEY = "tokyo-bay"
OUTSIDE_KEY = "outside"


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

    def create_table(self):
        self.cursor.execute(
            f"""
        CREATE TABLE IF NOT EXISTS "{TABLE_NAME}"(
            id SERIAL PRIMARY KEY,
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
        INSERT INTO "{TABLE_NAME}" (id, name, health, score, energy, location)
        VALUES ({self.player_id}, {self.monster_name}, 10, 0, 0, {OUTSIDE_KEY})
        """
        )
        self.connection.commit()

    def decrease_health(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET health = health - {amount}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("health")

    def increase_health(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET health = health + {amount}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("health")

    def increase_score(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET score = score + {amount}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("score")

    def decrease_score(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET score = score + {amount}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("score")

    def increase_energy(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET energy = energy + {amount}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("energy")

    def decrease_energy(self, amount):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET energy = energy + {amount}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("energy")

    def update_location(self, location):
        self.cursor.execute(
            f"""
        UPDATE "{TABLE_NAME}"
        SET location = {location}
        WHERE id = {self.player_id}
        """
        )
        self.connection.commit()
        return self.get_attribute("location")

    def get_attribute(self, attribute):
        self.cursor.execute(
            f"""
        SELECT {attribute} FROM "{TABLE_NAME}" WHERE id = {self.player_id}
        """
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_stats(self):
        self.cursor.execute(
            f"""
        SELECT name, health, score, energy, location FROM "{TABLE_NAME}" WHERE id = {self.player_id}
        """
        )
        result = self.cursor.fetchone()
        return {
            "name": result[0],
            "health": result[1],
            "score": result[2],
            "energy": result[3],
            "location": result[4],
        }
