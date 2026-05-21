// API service functions for user profile and authentication

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

interface Location {
  city: string;
  country: string;
}

interface Preferences {
  adults: string;
  children: string;
  childrenAgeList: string[];
  tripType: string;
  otherTripType: string;
  budget: string;
  budgetType: string;
  minStarRating: string;
  searchPreferences: string[];
}

interface ProfileUpdateRequest {
  username: string;
  email: string;
  language: string;
  location: Location;
  currency: string;
  preferences?: Preferences;
}

interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// Get authorization headers
const getAuthHeaders = () => {
  if (typeof window === 'undefined') return {};
  
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

// Update user profile
export const updateUserProfile = async (profileData: ProfileUpdateRequest): Promise<ApiResponse<any>> => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me/profile`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // Handle 400 errors with detailed messages
      if (response.status === 400) {
        return {
          error: errorData.detail || errorData.message || errorData.error || 'Invalid request data',
        };
      }
      
      return {
        error: errorData.message || errorData.detail || `HTTP error! status: ${response.status}`,
      };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error updating user profile:', error);
    return {
      error: error instanceof Error ? error.message : 'Failed to update profile',
    };
  }
};

// Get user profile
export const getUserProfile = async (): Promise<ApiResponse<any>> => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // Handle 400 errors with detailed messages
      if (response.status === 400) {
        return {
          error: errorData.detail || errorData.message || errorData.error || 'Invalid request data',
        };
      }
      
      return {
        error: errorData.message || errorData.detail || `HTTP error! status: ${response.status}`,
      };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return {
      error: error instanceof Error ? error.message : 'Failed to fetch user profile',
    };
  }
};

// Change user password
export const changeUserPassword = async (passwordData: PasswordChangeRequest): Promise<ApiResponse<any>> => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me/password`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(passwordData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // Handle 400 errors with detailed messages
      if (response.status === 400) {
        return {
          error: errorData.detail || errorData.message || errorData.error || 'Invalid request data',
        };
      }
      
      return {
        error: errorData.message || errorData.detail || `HTTP error! status: ${response.status}`,
      };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Error changing password:', error);
    return {
      error: error instanceof Error ? error.message : 'Failed to change password',
    };
  }
};
