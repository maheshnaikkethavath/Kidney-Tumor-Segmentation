import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
  },
});

export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    throw new Error(`Health check failed: ${error.message}`);
  }
};

export const predictSegmentation = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(`Prediction failed: ${error.response?.data?.detail || error.message}`);
  }
};

export const generateGradCAM = async (file, targetClass = 2) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`/gradcam?target_class=${targetClass}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(`GradCAM generation failed: ${error.response?.data?.detail || error.message}`);
  }
};

export const generateReport = async (file, patientId = 'Unknown', patientName = 'Unknown', format = 'html') => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(
      `/report?patient_id=${encodeURIComponent(patientId)}&patient_name=${encodeURIComponent(patientName)}&report_format=${format}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  } catch (error) {
    throw new Error(`Report generation failed: ${error.response?.data?.detail || error.message}`);
  }
};

export const compareModels = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/compare', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(`Model comparison failed: ${error.response?.data?.detail || error.message}`);
  }
};

export const listModels = async () => {
  try {
    const response = await api.get('/models');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to list models: ${error.message}`);
  }
};
