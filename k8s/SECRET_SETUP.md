# GARMINTOKENS Secret 생성 가이드

`GARMINTOKENS`는 Base64로 인코딩된 Garmin OAuth 토큰 데이터입니다.
`load_token()`이 매 프로세스 시작 시 이 env var를 최우선으로 시도하므로,
파드가 재시작돼도 `~/.garminconnect/` 디렉토리(ephemeral)가 사라진 것과 무관하게
정상적으로 재인증됩니다 — 별도 PVC 불필요.

## 1. 로컬에서 최초 인증

```bash
uv run python scripts/auth.py
# 이메일/비밀번호 입력 → ~/.garminconnect/garmin_tokens.json 생성됨
```

## 2. 토큰을 Base64로 인코딩

```bash
# garth 라이브러리는 토큰 디렉토리 전체를 tar로 묶어 base64 인코딩하는 방식을 기대함
# (garth.Client.dump()/configure(tokenstore=...) 참고 — 디렉토리 경로 대신
#  base64 문자열을 직접 넘기면 내부적으로 tar+base64 데이터로 처리됨)
cd ~/.garminconnect
tar -cf - . | base64 > /tmp/garmintokens.b64
```

> 정확한 인코딩 방식은 설치된 `garth`/`garminconnect` 버전의 `login(tokenstore=...)`
> 구현을 반드시 확인할 것 — 버전에 따라 단일 JSON base64 인코딩만으로 충분할 수도 있음.
> 안전하게는 로컬에서 `GARMINTOKENS=$(cat /tmp/garmintokens.b64)` 로 환경변수를 설정한 뒤
> `create_client()`가 성공적으로 로그인하는지 먼저 검증하고 나서 Secret에 반영한다.

## 3. K8s Secret 생성

```bash
kubectl -n garmin create secret generic garmin-tokens \
  --from-literal=GARMINTOKENS="$(cat /tmp/garmintokens.b64)"
```

## 4. SealedSecret으로 변환 (GitOps repo에 커밋하려면)

```bash
kubectl -n garmin get secret garmin-tokens -o yaml | \
  kubeseal --format yaml > sealed-garmin-tokens.yaml
```

`sealed-garmin-tokens.yaml`만 Git에 커밋 (평문 Secret은 커밋 금지).
