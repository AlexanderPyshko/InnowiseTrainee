-- list of rooms and students, which living in them
SELECT rooms.name, COUNT(students.id) AS student_count
FROM rooms
LEFT JOIN students ON rooms.id = students.room_id
GROUP BY rooms.name;

-- 5 rooms with the smallest average age among students
SELECT rooms.name, ROUND(AVG(EXTRACT(YEAR FROM AGE(students.birthday))), 2) AS avg_age
FROM rooms
LEFT JOIN students ON rooms.id = students.room_id
GROUP BY rooms.name
ORDER BY avg_age ASC
LIMIT 5;

-- 5 rooms with the maximum difference in students age
SELECT rooms.name,
       MAX(EXTRACT(YEAR FROM AGE(students.birthday))) - MIN(EXTRACT(YEAR FROM AGE(students.birthday))) AS age_difference
FROM rooms
LEFT JOIN students ON rooms.id = students.room_id
GROUP BY rooms.name
HAVING MAX(EXTRACT(YEAR FROM AGE(students.birthday))) IS NOT NULL
ORDER BY age_difference DESC
LIMIT 5;

-- List of rooms with different gender
SELECT rooms.name
FROM rooms
LEFT JOIN students ON rooms.id = students.room_id
GROUP BY rooms.name
HAVING COUNT(DISTINCT students.sex) > 1;

