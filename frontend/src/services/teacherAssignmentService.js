import { academicSubjects } from '../data/academic-data';

export function listTeacherAssignments() {
  return academicSubjects.map((subject) => ({
    subjectId: subject.id,
    subjectName: subject.name,
    teacher: subject.teacher,
    classes: subject.classes,
  }));
}
