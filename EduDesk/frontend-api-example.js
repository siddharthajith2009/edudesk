// Example of how to update your frontend to use Flask API
// This shows how to replace localStorage with API calls

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api'; // Change to your deployed URL

// Authentication functions
class AuthAPI {
    static async signup(name, email, password) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store JWT token
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    }
    
    static async login(email, password) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
            return { success: false, error: 'Network error' };
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
}

// Calendar API functions
class CalendarAPI {
    static async getEvents() {
        try {
            const response = await fetch(`${API_BASE_URL}/calendar/events`, {
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
            const response = await fetch(`${API_BASE_URL}/calendar/events`, {
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
    
    static async updateEvent(eventId, eventData) {
        try {
            const response = await fetch(`${API_BASE_URL}/calendar/events/${eventId}`, {
                method: 'PUT',
                headers: AuthAPI.getAuthHeaders(),
                body: JSON.stringify(eventData)
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to update event');
            }
        } catch (error) {
            console.error('Error updating event:', error);
            return null;
        }
    }
    
    static async deleteEvent(eventId) {
        try {
            const response = await fetch(`${API_BASE_URL}/calendar/events/${eventId}`, {
                method: 'DELETE',
                headers: AuthAPI.getAuthHeaders()
            });
            
            return response.ok;
        } catch (error) {
            console.error('Error deleting event:', error);
            return false;
        }
    }
}

// Mood Tracking API functions
class MoodAPI {
    static async getMoodEntries() {
        try {
            const response = await fetch(`${API_BASE_URL}/mood/entries`, {
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
            const response = await fetch(`${API_BASE_URL}/mood/entries`, {
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
    
    static async getMoodAnalytics() {
        try {
            const response = await fetch(`${API_BASE_URL}/mood/analytics`, {
                headers: AuthAPI.getAuthHeaders()
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch mood analytics');
            }
        } catch (error) {
            console.error('Error fetching mood analytics:', error);
            return null;
        }
    }
}

// Goals API functions
class GoalsAPI {
    static async getGoals() {
        try {
            const response = await fetch(`${API_BASE_URL}/goals/goals`, {
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
            const response = await fetch(`${API_BASE_URL}/goals/goals`, {
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
    
    static async updateGoalProgress(goalId, progress) {
        try {
            const response = await fetch(`${API_BASE_URL}/goals/goals/${goalId}/progress`, {
                method: 'PUT',
                headers: AuthAPI.getAuthHeaders(),
                body: JSON.stringify({ progress })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to update goal progress');
            }
        } catch (error) {
            console.error('Error updating goal progress:', error);
            return null;
        }
    }
}

// Study Sessions API functions
class StudyAPI {
    static async getStudySessions() {
        try {
            const response = await fetch(`${API_BASE_URL}/study/sessions`, {
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
            const response = await fetch(`${API_BASE_URL}/study/sessions`, {
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
    
    static async getStudyAnalytics() {
        try {
            const response = await fetch(`${API_BASE_URL}/study/analytics`, {
                headers: AuthAPI.getAuthHeaders()
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch study analytics');
            }
        } catch (error) {
            console.error('Error fetching study analytics:', error);
            return null;
        }
    }
}

// Example: Updated signup form handler
document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.querySelector('.signup-form');
    
    if (signupForm) {
        signupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            if (!name || !email || !password) {
                alert('Please fill in all fields.');
                return;
            }
            
            // Show loading state
            const submitBtn = document.querySelector('.signup-btn');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating Account...';
            submitBtn.disabled = true;
            
            try {
                const result = await AuthAPI.signup(name, email, password);
                
                if (result.success) {
                    // Redirect to dashboard
                    window.location.href = 'dashboard.html';
                } else {
                    alert(result.error || 'Signup failed. Please try again.');
                }
            } catch (error) {
                alert('An error occurred. Please try again.');
            } finally {
                // Reset button state
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});

// Example: Updated login form handler
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('.login-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                alert('Please fill in all fields.');
                return;
            }
            
            // Show loading state
            const submitBtn = document.querySelector('.login-btn');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Signing In...';
            submitBtn.disabled = true;
            
            try {
                const result = await AuthAPI.login(email, password);
                
                if (result.success) {
                    // Redirect to dashboard
                    window.location.href = 'dashboard.html';
                } else {
                    alert(result.error || 'Login failed. Please check your credentials.');
                }
            } catch (error) {
                alert('An error occurred. Please try again.');
            } finally {
                // Reset button state
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});

// Example: Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in for protected pages
    const protectedPages = ['dashboard.html', 'calendar.html', 'mood-tracker.html', 'goals.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage) && !AuthAPI.isLoggedIn()) {
        window.location.href = 'login.html';
    }
});

// Export for use in other files
window.AuthAPI = AuthAPI;
window.CalendarAPI = CalendarAPI;
window.MoodAPI = MoodAPI;
window.GoalsAPI = GoalsAPI;
window.StudyAPI = StudyAPI;
