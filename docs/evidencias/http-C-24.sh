B=${API_URL:-http://localhost:8000/api}; P="$SEED_USER_PASSWORD"
tok(){ curl -s -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$P\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["accessToken"])'; }
R=$(tok recepcion); O=$(tok odontologo); A=$(tok administrador)
Q=00000000-0000-0000-0000-000000000001; S=00000000-0000-0000-0000-000000000002
C1=00000000-0000-0000-0000-0000000000c1; C2=00000000-0000-0000-0000-0000000000c2; C3=00000000-0000-0000-0000-0000000000c3
B1=00000000-0000-0000-0000-0000000000b1; B2=00000000-0000-0000-0000-0000000000b2; CTRL=00000000-0000-0000-0000-0000000000d4
NX=00000000-0000-0000-0000-00000000ffff; J='Content-Type: application/json'; L=2026-11-16
req(){ t="$1"; shift; echo "== $t"; curl -s -o /var/tmp/r.json -w "HTTP %{http_code}\n" "$@"; }
show(){ cat /var/tmp/r.json; echo; }
resumen(){ python3 - <<'PY'
import json;d=json.load(open('/var/tmp/r.json'))
if isinstance(d,dict) and 'appointments' in d:
    for a in d['appointments']: print('  turno',a.get('startAt'),a.get('status'),a.get('professionalName'),a.get('chairName'),a.get('patientName'),a.get('serviceName'))
    print('  claves:',sorted(d.keys()))
    for k in d:
        if k!='appointments' and isinstance(d[k],list): print(f'  {k}: {len(d[k])} elementos')
else: print(' ',json.dumps(d,ensure_ascii=False)[:400])
PY
}
id(){ python3 -c 'import json;print(json.load(open("/var/tmp/r.json"))["id"])'; }
mk(){ curl -s -o /var/tmp/r.json -X POST $B/appointments -H "Authorization: Bearer $R" -H "$J" -d "{\"patientId\":\"$1\",\"professionalId\":\"$2\",\"chairId\":\"$3\",\"serviceId\":\"$CTRL\",\"startAt\":\"$4\"}"; id; }
A1=$(mk $C1 $Q $B1 ${L}T10:00:00-03:00); A2=$(mk $C2 $S $B2 ${L}T09:00:00-03:00); A3=$(mk $C3 $Q $B1 2026-11-17T10:00:00-03:00)
echo "preparacion: A1 Quiroga lun 10:00 Sillon 1; A2 Sosa lun 09:00 Sillon 2 (se cancela); A3 Quiroga mar 10:00 Sillon 1"
curl -s -o /dev/null -X POST $B/appointments/$A2/cancel -H "Authorization: Bearer $R"
curl -s -o /dev/null -X POST $B/professionals/$Q/blocks -H "Authorization: Bearer $O" -H "$J" -d "{\"startAt\":\"${L}T12:00:00-03:00\",\"endAt\":\"${L}T13:00:00-03:00\",\"reason\":\"Capacitacion\"}"
echo "preparacion: bloqueo de Quiroga lun 12:00-13:00"
req "1 agenda del lunes, recepcion (200; A1 y A2 cancelado, en orden)" "$B/agenda?from=$L&to=$L" -H "Authorization: Bearer $R"; resumen
req "2 filtro por profesional Quiroga (200; solo A1)" "$B/agenda?from=$L&to=$L&professionalId=$Q" -H "Authorization: Bearer $R"; resumen
req "3 filtro por Sillon 2 (200; solo A2)" "$B/agenda?from=$L&to=$L&chairId=$B2" -H "Authorization: Bearer $R"; resumen
req "4 filtros combinados Quiroga + Sillon 2 (200; ningun turno)" "$B/agenda?from=$L&to=$L&professionalId=$Q&chairId=$B2" -H "Authorization: Bearer $R"; resumen
req "5 odontologo ve la agenda completa, con el turno de Sosa (200)" "$B/agenda?from=$L&to=$L" -H "Authorization: Bearer $O"; resumen
req "6 semana lunes a domingo (200; A1, A2 y A3)" "$B/agenda?from=$L&to=2026-11-22" -H "Authorization: Bearer $A"; resumen
req "7 profesional inexistente (200; listas vacias)" "$B/agenda?from=$L&to=$L&professionalId=$NX" -H "Authorization: Bearer $R"; resumen
req "8 falta to (400)" "$B/agenda?from=$L" -H "Authorization: Bearer $R"; show
req "9 to anterior a from (400)" "$B/agenda?from=$L&to=2026-11-15" -H "Authorization: Bearer $R"; show
req "10 rango de 32 dias (400)" "$B/agenda?from=$L&to=2026-12-17" -H "Authorization: Bearer $R"; show
req "11 rango de 31 dias (200)" "$B/agenda?from=$L&to=2026-12-16" -H "Authorization: Bearer $R"; resumen
req "12 parametro desconocido status (400)" "$B/agenda?from=$L&to=$L&status=cancelado" -H "Authorization: Bearer $R"; show
req "13 UUID mal formado (400)" "$B/agenda?from=$L&to=$L&chairId=abc" -H "Authorization: Bearer $R"; show
req "14 fecha con formato invalido (400)" "$B/agenda?from=16-11-2026&to=$L" -H "Authorization: Bearer $R"; show
req "15 sin token (401)" "$B/agenda?from=$L&to=$L"; show
req "16 detalle de A1 (200, con nombres)" "$B/appointments/$A1" -H "Authorization: Bearer $O"; show
req "17 detalle de turno inexistente (404)" "$B/appointments/$NX" -H "Authorization: Bearer $R"; show