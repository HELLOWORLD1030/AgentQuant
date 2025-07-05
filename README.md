## 基于AgentScope与Qwen系列模型的金融知识问答系统
### 实现功能
- 金融专业语义检索
- 自然语言查询分析
- PDF/JSON多源数据融合处理
- 回答置信度评估
- 市场分析报告生成
### 系统架构
![Untitled diagram _ Mermaid Chart-2025-07-02-131617](https://github.com/user-attachments/assets/293fe31c-941a-4036-9d77-3d5de3fcc03b)
### Agent配置
目前分配了4个Agent，分别是
1. 对话管理器
2. 检索Agent
3. 生成Agent
4. 置信度判断Agent

### 安装部署
#### ollama与qwen安装
```shell
curl -fsSL https://ollama.com/install.sh | sh
ollama run qwen3:4b
ollama pull nomic-embed-text
```
#### 代码
```shell
git clone https://github.com/HELLOWORLD1030/AgentQuant
cd AgentQuant
conda env create -f environment.yml
conda activate quantAgent
# 确保Ollama在工作状态
python main.py
```
