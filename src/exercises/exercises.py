"""Exercises: ORM fundamentals.

Implement the TODO functions. Autograder will test them.
"""

from typing import Optional
from flask import request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from unicodedata import lookup

from src.exercises.extensions import db
from src.exercises.models import Student, Grade, Assignment


from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Student, Grade, Assignment



# ===== BASIC CRUD =====

def create_student(name: str, email: str) -> Student:
    """TODO: Create and commit a Student; handle duplicate email.
    If email is duplicate:
      - rollback
      - raise ValueError("duplicate email")
    """


    a = Student(name=name, email=email)
    db.session.add(a)
    try:
        db.session.commit()
        return a
    except IntegrityError:
        db.session.rollback()
        raise ValueError("duplicate email")


def find_student_by_email(email: str) -> Optional[Student]:
    """TODO: Return Student by email or None."""
    return Student.query.filter_by(email=email).first()


def add_grade(student_id: int, assignment_id: int, score: int) -> Grade:
    """TODO: Add a Grade for the student+assignment and commit.

    If student doesn't exist: raise LookupError
    If assignment doesn't exist: raise LookupError
    If duplicate grade: raise ValueError("duplicate grade")
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError(f"Student {student_id} does not exist.")

    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError(f"Assignment {assignment_id} does not exist.")

    grade = Grade(student_id=student_id, assignment_id=assignment_id, score=score)
    db.session.add(grade)
    try:
        db.session.commit()
        return grade
    except IntegrityError:
        db.session.rollback()
        raise ValueError("duplicate grade")

def average_percent(student_id: int) -> float:
    """TODO: Return student's average percent across assignments.

    percent per grade = score / assignment.max_points * 100

    If student doesn't exist: raise LookupError
    If student has no grades: return 0.0
    """

    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError(f"Student {student_id} does not exist.")

    grades_with_assignments = (
        db.session.query(Grade, Assignment)
        .join(Assignment, Grade.assignment_id == Assignment.id)
        .filter(Grade.student_id == student_id)
        .all()
    )

    if not grades_with_assignments:
        return 0.0

    total_percent = 0.0
    for grade, assignment in grades_with_assignments:
        percent = (grade.score / assignment.max_points) * 100
        total_percent += percent

    average = total_percent / len(grades_with_assignments)
    return average

# ===== QUERYING & FILTERING =====

def get_all_students() -> list[Student]:
    """TODO: Return all students in database, ordered by name."""
    return Student.query.order_by(Student.name).all()


def get_assignment_by_title(title: str) -> Optional[Assignment]:
    """TODO: Return assignment by title or None."""
    return Assignment.query.filter_by(title=title).first()


def get_student_grades(student_id: int) -> list[Grade]:
    """TODO: Return all grades for a student, ordered by assignment title.

    If student doesn't exist: raise LookupError
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError

    return (
        Grade.query
        .join(Assignment, Grade.assignment_id == Assignment.id)
        .filter(Grade.student_id == student_id)
        .order_by(Assignment.title)
        .all()
    )

def get_grades_for_assignment(assignment_id: int) -> list[Grade]:
    """TODO: Return all grades for an assignment, ordered by student name.

    If assignment doesn't exist: raise LookupError
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError

    return (
        Grade.query
        .join(Student, Grade.student_id == Student.id)
        .filter(Grade.assignment_id == assignment_id)
        .order_by(Student.name)
        .all()
    )

# ===== AGGREGATION =====

def total_student_grade_count() -> int:
    """TODO: Return total number of grades in database."""
    return db.session.query(Grade).count()


def highest_score_on_assignment(assignment_id: int) -> Optional[int]:
    """TODO: Return the highest score on an assignment, or None if no grades.

    If assignment doesn't exist: raise LookupError
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError(f"Assignment {assignment_id} does not exist.")

    result = (
        db.session.query(func.max(Grade.score))
        .filter(Grade.assignment_id == assignment_id)
        .scalar()
    )

    return result


def class_average_percent() -> float:
    """TODO: Return average percent across all students and all assignments.

    percent per grade = score / assignment.max_points * 100
    Return average of all these percents.
    If no grades: return 0.0
    """
    avg_expr = func.avg(Grade.score * 100.0 / Assignment.max_points)

    result = (
        db.session.query(avg_expr)
        .select_from(Grade)  # explicitly start from Grade
        .join(Assignment, Grade.assignment_id == Assignment.id)
        .scalar()
    )

    return float(result) if result is not None else 0.0


def student_grade_count(student_id: int) -> int:
    """TODO: Return number of grades for a student.

    If student doesn't exist: raise LookupError
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError
    return Grade.query.filter(Grade.student_id == student_id).count()


# ===== UPDATING & DELETION =====

def update_student_email(student_id: int, new_email: str) -> Student:
    """TODO: Update a student's email and commit.

    If student doesn't exist: raise LookupError
    If new email is duplicate: rollback and raise ValueError("duplicate email")
    Return the updated student.
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError(f"Student {student_id} does not exist.")

    student.email = new_email
    try:
        db.session.commit()
        return student
    except IntegrityError:
        db.session.rollback()
        raise ValueError("duplicate email")


def delete_student(student_id: int) -> None:
    """TODO: Delete a student and all their grades; commit.

    If student doesn't exist: raise LookupError
    """
    student = db.session.get(Student, student_id)
    if not student:
        raise LookupError(f"Student {student_id} does not exist.")

    # Delete all grades associated with the student
    Grade.query.filter_by(student_id=student_id).delete()

    # Delete the student
    db.session.delete(student)
    db.session.commit()


def delete_grade(grade_id: int) -> None:
    """TODO: Delete a grade by id; commit.

    If grade doesn't exist: raise LookupError
    """
    grade = db.session.get(Grade, grade_id)
    if not grade:
        raise LookupError(f"Grade {grade_id} does not exist.")

    db.session.delete(grade)
    db.session.commit()


# ===== FILTERING & FILTERING WITH AGGREGATION =====

def students_with_average_above(threshold: float) -> list[Student]:
    avg_percent = (
        db.session.query(
            Student,
            func.avg(Grade.score * 100.0 / Assignment.max_points).label("avg_percent")
        )
        .join(Grade, Grade.student_id == Student.id)
        .join(Assignment, Grade.assignment_id == Assignment.id)
        .group_by(Student.id)
        .having(func.avg(Grade.score * 100.0 / Assignment.max_points) > threshold)
        .order_by(func.avg(Grade.score * 100.0 / Assignment.max_points).desc())
        .all()
    )

    return [student for student, _ in avg_percent]


def assignments_without_grades() -> list[Assignment]:
    """TODO: Return assignments that have no grades yet, ordered by title."""
    return (
        Assignment.query
        .outerjoin(Grade)
        .filter(Grade.id == None)
        .order_by(Assignment.title)
        .all()
    )

def top_scorer_on_assignment(assignment_id: int) -> Optional[Student]:
    """TODO: Return the Student with the highest score on an assignment.

    If assignment doesn't exist: raise LookupError
    If no grades on assignment: return None
    If tie (multiple students with same high score): return any one
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise LookupError(f"Assignment {assignment_id} does not exist.")

    top_grade = (
        Grade.query
        .filter(Grade.assignment_id == assignment_id)
        .order_by(Grade.score.desc())
        .first()
    )

    if not top_grade:
        return None

    return db.session.get(Student, top_grade.student_id)

