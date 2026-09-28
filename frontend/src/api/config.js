import { createHttp } from '@/api/http'

const http = createHttp(15000)

export const configApi = {
  // 模型注册表
  listRegistry:      ()           => http.get('/config/registry'),
  addModel:          (data)       => http.post('/config/registry', data),
  updateModel:       (id, data)   => http.put(`/config/registry/${id}`, data),
  deleteModel:       (id)         => http.delete(`/config/registry/${id}`),
  availableModels:   ()           => http.get('/config/available-models'),
}
