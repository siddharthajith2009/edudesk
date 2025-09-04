// EduDesk API Configuration
// This file connects your frontend to the Flask backend

const API_CONFIG = {
    // Local development
    BASE_URL: 'http://localhost:5001/api',
    
    // Production (update this when you deploy)
    // BASE_URL: 'https://your-deployed-api.com/api',
    
    // API endpoints
    ENDPOINTS: {
        // Authentication
        SIGNUP: '/auth/signup',
        LOGIN: '/auth/login',
        PROFILE: '/auth/profile',
        
        // Calendar
        CALENDAR_EVENTS: '/calendar/events',
        
        // Mood tracking
        MOOD_ENTRIES: '/mood/entries',
        MOOD_ANALYTICS: '/mood/analytics',
        
        // Journal
        JOURNAL_ENTRIES: '/journal/entries',
        
        // Goals
        GOALS: '/goals/goals',
        
        // Study sessions
        STUDY_SESSIONS: '/study/sessions',
        STUDY_ANALYTICS: '/study/analytics',
        
        // Blog
        BLOG_POSTS: '/blog/posts',
        
        // Alarms
        ALARMS: '/alarms/alarms',
        
        // Documents
        DOCUMENTS: '/documents/documents',
        
        // Analytics
        DASHBOARD_ANALYTICS: '/analytics/dashboard'
    }
};

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return API_CONFIG.BASE_URL + endpoint;
}

// Authentication helper functions
class AuthAPI {
    static async signup(name, email, password) {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.SIGNUP), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store JWT token and user data
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error. Make sure the Flask backend is running on port 5001.' };
        }
    }
    
    static async login(email, password) {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.LOGIN), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error. Make sure the Flask backend is running on port 5001.' };
        }
    }
    
    static getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    }
    
    static isLoggedIn() {
        return !!localStorage.getItem('access_token');
    }
    
    static logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    }
    
    static getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }
}

// Calendar API functions
class CalendarAPI {
    static async getEvents() {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.CALENDAR_EVENTS), {
                headers: AuthAPI.getAuthHeaders()
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch events');
            }
        } catch (error) {
            console.error('Error fetching events:', error);
            return [];
        }
    }
    
    static async createEvent(eventData) {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.CALENDAR_EVENTS), {
                method: 'POST',
                headers: AuthAPI.getAuthHeaders(),
                body: JSON.stringify(eventData)
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to create event');
            }
        } catch (error) {
            console.error('Error creating event:', error);
            return null;
        }
    }
}

// Mood API functions
class MoodAPI {
    static async getMoodEntries() {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.MOOD_ENTRIES), {
                headers: AuthAPI.getAuthHeaders()
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch mood entries');
            }
        } catch (error) {
            console.error('Error fetching mood entries:', error);
            return [];
        }
    }
    
    static async createMoodEntry(mood, moodLevel, notes = '') {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.MOOD_ENTRIES), {
                method: 'POST',
                headers: AuthAPI.getAuthHeaders(),
                body: JSON.stringify({ mood, mood_level: moodLevel, notes })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to create mood entry');
            }
        } catch (error) {
            console.error('Error creating mood entry:', error);
            return null;
        }
    }
}

// Goals API functions
class GoalsAPI {
    static async getGoals() {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.GOALS), {
                headers: AuthAPI.getAuthHeaders()
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch goals');
            }
        } catch (error) {
            console.error('Error fetching goals:', error);
            return [];
        }
    }
    
    static async createGoal(goalData) {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.GOALS), {
                method: 'POST',
                headers: AuthAPI.getAuthHeaders(),
                body: JSON.stringify(goalData)
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to create goal');
            }
        } catch (error) {
            console.error('Error creating goal:', error);
            return null;
        }
    }
}

// Study API functions
class StudyAPI {
    static async getStudySessions() {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.STUDY_SESSIONS), {
                headers: AuthAPI.getAuthHeaders()
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch study sessions');
            }
        } catch (error) {
            console.error('Error fetching study sessions:', error);
            return [];
        }
    }
    
    static async createStudySession(duration, subject, notes = '', sessionType = 'pomodoro') {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.STUDY_SESSIONS), {
                method: 'POST',
                headers: AuthAPI.getAuthHeaders(),
                body: JSON.stringify({ duration, subject, notes, session_type: sessionType })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to create study session');
            }
        } catch (error) {
            console.error('Error creating study session:', error);
            return null;
        }
    }
}

// Make API classes available globally
window.AuthAPI = AuthAPI;
window.CalendarAPI = CalendarAPI;
window.MoodAPI = MoodAPI;
window.GoalsAPI = GoalsAPI;
window.StudyAPI = StudyAPI;
window.API_CONFIG = API_CONFIG;
