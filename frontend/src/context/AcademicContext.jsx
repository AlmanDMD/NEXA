import React, { createContext, useContext, useMemo, useState } from 'react';
import {
  academicAlerts,
  academicClasses,
  academicDashboard,
  academicStudents,
  academicSubjects,
  getAcademicStudentProfile,
  initialAttendanceMap,
  initialHelpRequests,
  initialPracticalActivities,
  initialSelfAssessmentCompetencies,
  initialStudentBadges,
  initialWallPosts,
  initialWorkshopModules,
} from '../data/academic-data';

const AcademicDataContext = createContext(null);

export function AcademicDataProvider({ children }) {
  const [role, setRole] = useState('teacher'); // 'teacher' | 'student'
  const [activeStudentId, setActiveStudentId] = useState('s-01');
  const [studentsList, setStudentsList] = useState(academicStudents);
  const [classesList, setClassesList] = useState(academicClasses);
  const [subjectsList, setSubjectsList] = useState(academicSubjects);
  const [alertsList, setAlertsList] = useState(academicAlerts);
  const [customHistoryMap, setCustomHistoryMap] = useState({});
  const [attendanceMap, setAttendanceMap] = useState(initialAttendanceMap);
  const [workshopModules] = useState(initialWorkshopModules);
  const [practicalActivities, setPracticalActivities] = useState(initialPracticalActivities);
  const [helpRequests, setHelpRequests] = useState(initialHelpRequests);
  const [wallPosts, setWallPosts] = useState(initialWallPosts);
  const [competencies, setCompetencies] = useState(initialSelfAssessmentCompetencies);
  const [badges] = useState(initialStudentBadges);

  const toggleAlertFollow = (id) => {
    setAlertsList((prev) =>
      prev.map((item) => (item.id === id ? { ...item, followed: !item.followed } : item)),
    );
  };

  const addStudent = ({ name, registration, className, course, average = 7.5, attendance = 92 }) => {
    const numAvg = Number(average) || 7.5;
    const numAtt = Number(attendance) || 92;
    const status = numAvg < 5.5 || numAtt < 75 ? 'Crítico' : numAvg < 7 || numAtt < 85 ? 'Atenção' : 'Regular';
    const newStudent = {
      id: `s-${Date.now()}`,
      name,
      registration: registration || `2024.${Math.floor(1000 + Math.random() * 9000)}`,
      className,
      course: course || `Técnico em ${className.split(' ')[0]}`,
      average: numAvg,
      attendance: numAtt,
      status,
      updatedAt: 'Agora mesmo',
    };
    setStudentsList((prev) => [newStudent, ...prev]);
    return newStudent;
  };

  const addClassGroup = ({ name, course, students = 30 }) => {
    const newClass = {
      id: `c-${Date.now()}`,
      name,
      course,
      students: Number(students) || 30,
      average: 7.5,
      attendance: 90,
      attentionCount: 2,
      status: 'Em andamento',
    };
    setClassesList((prev) => [newClass, ...prev]);
  };

  const addSubject = ({ name, teacher, classes }) => {
    const newSubject = {
      id: `d-${Date.now()}`,
      name,
      teacher: teacher || 'Prof. Mariana Costa',
      classes: classes || 'Eletrotécnica 2A',
      average: 7.6,
      attendance: 91,
      attentionCount: 2,
    };
    setSubjectsList((prev) => [newSubject, ...prev]);
  };

  const addStudentHistory = (studentId, { title, detail, author = 'Prof. Mariana Costa' }) => {
    const entry = {
      date: 'Hoje',
      author,
      title,
      detail,
    };
    setCustomHistoryMap((prev) => ({
      ...prev,
      [studentId]: [entry, ...(prev[studentId] || [])],
    }));
  };

  const getStudentProfileById = (studentId) => {
    const found = studentsList.find((s) => s.id === studentId) || studentsList[0];
    if (!found) return null;
    return getAcademicStudentProfile(found, customHistoryMap);
  };

  const setStudentAttendanceStatus = (studentId, statusChar) => {
    setAttendanceMap((prev) => ({
      ...prev,
      [studentId]: statusChar,
    }));
  };

  const markAllPresentInClass = (className) => {
    setAttendanceMap((prev) => {
      const next = { ...prev };
      studentsList
        .filter((s) => !className || className === 'Todas' || s.className === className)
        .forEach((s) => {
          next[s.id] = 'P';
        });
      return next;
    });
  };

  const togglePracticalCompletion = (activityId, studentId) => {
    setPracticalActivities((prev) =>
      prev.map((act) => {
        if (act.id !== activityId) return act;
        const exists = act.completedStudentIds.includes(studentId);
        return {
          ...act,
          completedStudentIds: exists
            ? act.completedStudentIds.filter((id) => id !== studentId)
            : [...act.completedStudentIds, studentId],
        };
      }),
    );
  };

  const addPracticalActivity = ({ title, className, criteria, dueDate, moduleId = 'm-01' }) => {
    const newAct = {
      id: `pa-${Date.now()}`,
      moduleId,
      className,
      title,
      criteria,
      dueDate: dueDate || 'Hoje · Oficina SENAI',
      maxScore: 10,
      completedStudentIds: [],
    };
    setPracticalActivities((prev) => [newAct, ...prev]);
  };

  const submitHelpRequest = ({ subject, bench, urgency, question }) => {
    const activeStudent = studentsList.find((s) => s.id === activeStudentId) || studentsList[0];
    const newReq = {
      id: `hr-${Date.now()}`,
      studentId: activeStudent.id,
      studentName: activeStudent.name,
      className: activeStudent.className,
      subject,
      bench: bench || 'Bancada 01',
      urgency: urgency || 'Média',
      status: 'Pendente',
      createdAt: 'Agora mesmo',
      question,
      reply: '',
    };
    setHelpRequests((prev) => [newReq, ...prev]);
  };

  const replyHelpRequest = (requestId, replyText) => {
    setHelpRequests((prev) =>
      prev.map((req) =>
        req.id === requestId
          ? {
              ...req,
              status: 'Respondido',
              reply: replyText,
            }
          : req,
      ),
    );
  };

  const addWallPost = ({ title, content, targetClass = 'Todas as turmas', tag = 'Aviso' }) => {
    const newPost = {
      id: `wp-${Date.now()}`,
      author: 'Prof. Mariana Costa',
      role: 'Docente SENAI',
      targetClass,
      title,
      content,
      date: 'Agora mesmo',
      tag,
    };
    setWallPosts((prev) => [newPost, ...prev]);
  };

  const updateCompetencySelfLevel = (compId, level) => {
    setCompetencies((prev) =>
      prev.map((c) => (c.id === compId ? { ...c, studentLevel: level } : c)),
    );
  };

  const activeStudent = useMemo(
    () => studentsList.find((s) => s.id === activeStudentId) || studentsList[0],
    [studentsList, activeStudentId],
  );

  const value = useMemo(
    () => ({
      role,
      setRole,
      activeStudentId,
      setActiveStudentId,
      activeStudent,
      dashboard: {
        data: {
          ...academicDashboard,
          totalStudents: studentsList.length > 12 ? 154 + (studentsList.length - 12) : 154,
        },
        isPending: false,
        isError: false,
      },
      students: { data: studentsList, isPending: false, isError: false },
      classes: { data: classesList, isPending: false, isError: false },
      subjects: { data: subjectsList, isPending: false, isError: false },
      alerts: { data: alertsList, isPending: false, isError: false },
      toggleAlertFollow,
      addStudent,
      addClassGroup,
      addSubject,
      addStudentHistory,
      getStudentProfileById,
      attendanceMap,
      setStudentAttendanceStatus,
      markAllPresentInClass,
      workshopModules,
      practicalActivities,
      togglePracticalCompletion,
      addPracticalActivity,
      helpRequests,
      submitHelpRequest,
      replyHelpRequest,
      wallPosts,
      addWallPost,
      competencies,
      updateCompetencySelfLevel,
      badges,
    }),
    [
      role,
      activeStudentId,
      activeStudent,
      studentsList,
      classesList,
      subjectsList,
      alertsList,
      customHistoryMap,
      attendanceMap,
      workshopModules,
      practicalActivities,
      helpRequests,
      wallPosts,
      competencies,
      badges,
    ],
  );

  return <AcademicDataContext.Provider value={value}>{children}</AcademicDataContext.Provider>;
}

export function useAcademicQueries() {
  const queries = useContext(AcademicDataContext);
  if (!queries) {
    throw new Error('AcademicDataProvider não foi configurado.');
  }
  return queries;
}

