import ollama

article = """
LG디스플레이는 최근 '이형(異形) 디스플레이' 설계에 AI 알고리즘을 도입해 괄목할 성과를 거뒀다. 
스마트폰의 곡면이나 베젤 디자인에 맞춘 회로 설계는 그동안 오류가 잦아 평균 1개월이 소요됐으나, AI 도입 후 8시간으로 단축됐다.
생산 현장에서도 AI의 활약은 독보적이다. 
140여 개의 OLED 공정 데이터를 실시간 분석하는 'AI 생산 체계'는 과거 3주가 걸리던 품질 이상 원인 분석을 단 2일로 줄였다. 
수십 년간 축적된 숙련공의 노하우를 학습한 AI가 문제 지점과 해결책을 즉각 제시하기 때문이다. 
LG디스플레이는 이를 통해 연간 약 2,000억 원 이상의 비용 절감이 가능할 것으로 보고 있다.
"""

# 키워드 추출
print("=== 키워드 추출 ===")
response = ollama.chat(
    model="gemma3:4b",
    messages=[
        {"role": "system", "content": "주어진 텍스트에서 핵심 키워드 5개를 추출하세요. 키워드만 쉼표로 구분하여 나열하세요."},
        {"role": "user", "content": article}
    ]
)
print(response["message"]["content"])

# 요약
print("\n=== 3줄 요약 ===")
response = ollama.chat(
    model="gemma3:4b",
    messages=[
        {"role": "system", "content": "주어진 텍스트를 정확히 3줄로 요약하세요. 각 줄은 한 문장으로 작성하세요."},
        {"role": "user", "content": article}
    ]
)
print(response["message"]["content"])