import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
});

// Interceptor para adicionar o token JWT automaticamente
api.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("sga_token");
        if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ─────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────
export const login = (username: string, password: string) =>
    api.post("/api/auth/login", { username, password });

// ─────────────────────────────────────────
// STUDENTS
// ─────────────────────────────────────────
export const getStudents = (params?: { class_name?: string; limit?: number }) =>
    api.get("/api/students", { params });

// ─────────────────────────────────────────
// ADMIN
// ─────────────────────────────────────────
export const getClasses = () => api.get("/api/admin/classes");
export const createClass = (data: object) => api.post("/api/admin/classes", data);
export const updateClass = (id: number, data: object) => api.put(`/api/admin/classes/${id}`, data);
export const deleteClass = (id: number) => api.delete(`/api/admin/classes/${id}`);

export const getDisciplines = () => api.get("/api/admin/disciplines");
export const createDiscipline = (data: object) => api.post("/api/admin/disciplines", data);
export const updateDiscipline = (id: number, data: object) => api.put(`/api/admin/disciplines/${id}`, data);
export const deleteDiscipline = (id: number) => api.delete(`/api/admin/disciplines/${id}`);

export const getUsers = () => api.get("/api/admin/users");
export const createUser = (data: object) => api.post("/api/admin/users", data);
export const toggleUserActive = (id: string) => api.put(`/api/admin/users/${id}/toggle-active`);

export const getCompetencies = (params?: object) => api.get("/api/admin/competencies", { params });
export const createCompetency = (data: object) => api.post("/api/admin/competencies", data);
export const updateCompetency = (id: number, data: object) => api.put(`/api/admin/competencies/${id}`, data);
export const deleteCompetency = (id: number) => api.delete(`/api/admin/competencies/${id}`);

export const getTeacherClass = () => api.get("/api/admin/teacher-class");
export const createTeacherClass = (data: object) => api.post("/api/admin/teacher-class", data);
export const deleteTeacherClass = (id: number) => api.delete(`/api/admin/teacher-class/${id}`);

export const uploadStudentsCSV = (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/api/admin/students/upload-csv", form, {
        headers: { "Content-Type": "multipart/form-data" },
    });
};

// ─────────────────────────────────────────
// PLANEJAMENTO
// ─────────────────────────────────────────
export const getPlanningBimester = (params: object) =>
    api.get("/api/planning/bimester", { params });
export const addToPlanningBimester = (data: object) =>
    api.post("/api/planning/bimester", data);
export const removeFromPlanningBimester = (id: string) =>
    api.delete(`/api/planning/bimester/${id}`);

export const getObjectives = (params: object) => api.get("/api/planning/objectives", { params });
export const generateObjectives = (data: object) => api.post("/api/planning/objectives/generate", data);
export const updateObjective = (id: string, data: object) => api.put(`/api/planning/objectives/${id}`, data);
export const approveObjective = (id: string, data: object) => api.post(`/api/planning/objectives/${id}/approve`, data);
export const submitObjective = (id: string) => api.post(`/api/planning/objectives/${id}/submit`);

export const getRubrics = (objectiveId: string) => api.get(`/api/planning/rubrics/${objectiveId}`);
export const generateRubrics = (objectiveId: string, data: object) =>
    api.post(`/api/planning/rubrics/${objectiveId}/generate`, data);
export const approveRubricLevel = (rubricLevelId: string, data: object) =>
    api.put(`/api/planning/rubrics/level/${rubricLevelId}`, data);

// ─────────────────────────────────────────
// BNCC + AVALIAÇÃO
// ─────────────────────────────────────────
export const getBnccSkills = (params?: object) => api.get("/api/bncc-skills", { params });
export const getAssessments = (params?: object) => api.get("/api/assessments", { params });

// ─────────────────────────────────────────
// ANALYTICS
// ─────────────────────────────────────────
export const getDashboardData = (params?: object) => api.get("/api/analytics/dashboard", { params });
export const getStudentEvolution = (studentId: string, params?: object) =>
    api.get(`/api/analytics/evolution/${studentId}`, { params });
export const getClassRadar = (className: string, params?: object) =>
    api.get(`/api/analytics/class-radar/${className}`, { params });
export const getHeatmapData = (assessments: object[]) =>
    api.post("/api/analytics/heatmap", { assessments });

// AI legado
export const generateRubric = (data: { skill_code: string; objective: string }) =>
    api.post("/api/ai/rubric", data);
