# lib/review.py

from __init__ import CURSOR, CONN
from employee import Employee

class Review:
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        self.id = id
        self.year = year
        self.summary = summary
        self.employee_id = employee_id

    def __repr__(self):
        return f"<Review {self.id}: {self.year}, {self.summary}, Employee ID: {self.employee_id}>"

    @classmethod
    def create_table(cls):
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        CURSOR.execute("DROP TABLE IF EXISTS reviews")
        CONN.commit()

    def save(self):
        """Insert or update this Review into the database and cache it."""
        if self.id is None:
            CURSOR.execute(
                "INSERT INTO reviews (year, summary, employee_id) VALUES (?, ?, ?)",
                (self.year, self.summary, self.employee_id)
            )
            CONN.commit()
            self.id = CURSOR.lastrowid
        else:
            CURSOR.execute(
                "UPDATE reviews SET year = ?, summary = ?, employee_id = ? WHERE id = ?",
                (self.year, self.summary, self.employee_id, self.id)
            )
            CONN.commit()
        Review.all[self.id] = self

    @classmethod
    def create(cls, year, summary, employee_id):
        """Convenience: make a new Review, save it, and return it."""
        review = cls(year, summary, employee_id)
        review.save()
        return review

    @classmethod
    def instance_from_db(cls, row):
        """Return a cached Review for this row, or build & cache a new one."""
        _id, year, summary, emp_id = row
        if _id in cls.all:
            inst = cls.all[_id]
            inst.year = year
            inst.summary = summary
            inst.employee_id = emp_id
            return inst
        inst = cls(year, summary, emp_id, id=_id)
        cls.all[_id] = inst
        return inst

    @classmethod
    def find_by_id(cls, id):
        row = CURSOR.execute("SELECT * FROM reviews WHERE id = ?", (id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def get_all(cls):
        rows = CURSOR.execute("SELECT * FROM reviews").fetchall()
        return [cls.instance_from_db(r) for r in rows]

    def update(self):
        """Persist any changes to year/summary/employee_id back to the table."""
        if not self.id:
            raise ValueError("Can't update a Review that hasn't been saved")
        CURSOR.execute(
            "UPDATE reviews SET year = ?, summary = ?, employee_id = ? WHERE id = ?",
            (self.year, self.summary, self.employee_id, self.id)
        )
        CONN.commit()

    def delete(self):
        """Remove this review row and purge from cache."""
        if not self.id:
            raise ValueError("Can't delete a Review that hasn't been saved")
        CURSOR.execute("DELETE FROM reviews WHERE id = ?", (self.id,))
        CONN.commit()
        del Review.all[self.id]
        self.id = None

  
    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        if not isinstance(value, int) or value < 2000:
            raise ValueError("year must be an integer ≥ 2000")
        self._year = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("summary must be a non-empty string")
        self._summary = text

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, emp_id):
        if not (isinstance(emp_id, int) and Employee.find_by_id(emp_id)):
            raise ValueError("employee_id must reference an existing Employee")
        self._employee_id = emp_id
