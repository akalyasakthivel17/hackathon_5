** Overview

This platform is a full-stack, API-driven HR & Workforce Management System designed to digitize and automate employee lifecycle operations, performance tracking, and organizational engagement.

The system is built using:

    * Django REST Framework

    * MongoDB (PyMongo)

Employee Directory & Onboarding ⭐ CRITICAL

Features

    * Employee CRUD (Soft delete)

    * Auto Employee ID generation (EMP001)

    * Store employee documents as Base64

    * Role-based employee profile access

    * Welcome email with auto-generated password

Authentication & Authorization ⭐ CRITICAL

Features

    * Email + Password login

    * Role returned during login (User | Manager | HR)

    * Sign-out API

    * Role-based API behavior

Grievance Management System ⭐ HIGH VALUE

Role	Access Scope
User	Own grievances only
HR	All grievances
Manager	HR grievances + grievances older than 7 days

Features

    * Raise grievance (category, priority, description)

    * HR replies with threaded conversation

    * Status tracking (OPEN → IN_PROGRESS → RESOLVED)

    * Replies enriched with employee name & role

    * Clean conversation-style API response

Task & Performance Management ⭐ HIGH VALUE
Features

    * Task creation & assignment

    * Status lifecycle: ASSIGNED → IN_PROGRESS → COMPLETED
    
    * Reassignment support

    * Comment system

    * Soft delete

    * Automated performance scoring

Automated Performance Scoring Formula

When a task is marked COMPLETED, score is calculated automatically.

Final Score Formula

Final Score = (Manager Rating × 10)
            + Deadline Score
            + Quality Score

| Component      | Logic                             | Max |
| -------------- | --------------------------------- | --- |
| Manager Rating | rating × 10                       | 50  |
| Deadline       | On-time: +30, Late: +10           | 30  |
| Quality        | Completion keywords: +20 else +10 | 20  |

Maximum Score: 100

Example:

Manager Rating = 4
Deadline = On-time
Comment = "Task completed successfully"

Final Score = (4 × 10) + 30 + 20 = 90

Dashboard & Analytics ⭐ CRITICAL
Employee Metrics

    * Total active employees

    * Department-wise count

Task Metrics (User-Specific)

    * Tasks assigned this month

    * Tasks completed

    * Remaining tasks

6️⃣ Attendance & Leave Management ⭐ CRITICAL
Attendance Management

Employee check-in / check-out with timestamp

    * Working hours calculation

    * Attendance history

    * Monthly attendance reports

Working Hours Formula
    Working Hours = Check-out Time − Check-in Time

Leave Management    


| Leave Type | Annual Balance |
| ---------- | -------------- |
| Casual     | 12             |
| Sick       | 12             |
| Vacation   | 15             |

Features

    * Apply leave (type, date range, reason)

    * Manager approval / rejection

    * Automatic leave balance deduction

    * Leave calendar view

    * Leave history & reports

Company Events & Engagement ⭐ BONUS POINTS
Features

    * Upcoming birthdays dashboard

    * Company events calendar:

    * Holidays

    * Meetings

    * Celebrations

    * Announcements board

    * Kudos / Recognition wall

    * Post appreciation

Travel & Expense Management ⭐ BONUS POINTS
Features

Travel request submission

Expense receipt upload (Base64)

Manager approval workflow

Reimbursement status tracking

Expense reports