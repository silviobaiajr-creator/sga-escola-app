import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
});

// Students
export const getStudents = () => api.get("/api/students");

// AI endpoints
export const generateObjectives = (data: {
    skill_code: string;
    skill_description: string;
    quantity?: number;
    discipline_name?: string;
}) => api.post("/api/ai/objectives", data);

export const generateRubric = (data: { skill_code: string; objective: string }) =>
    api.post("/api/ai/rubric", data);

// Analytics
export const getHeatmapData = (assessments: object[]) =>
    api.post("/api/analytics/heatmap", { assessments });
