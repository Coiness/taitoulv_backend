// API 基础URL
const API_BASE_URL = 'http://localhost:3001';

// 通用请求函数
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// 测试后端连接
export async function testBackendConnection() {
  return fetchAPI('/api/test');
}

// 上传图片
export async function uploadImage(file: File) {
  const formData = new FormData();
  formData.append('image', file);

  return fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  }).then(res => res.json());
}