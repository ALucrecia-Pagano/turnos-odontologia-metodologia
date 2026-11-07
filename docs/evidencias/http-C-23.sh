B=${API_URL:-http://localhost:8000/api}; P="$SEED_USER_PASSWORD"
PSQL="docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -At"
tok(){ curl -s -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$P\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["accessToken"])'; }
R=$(tok recepcion); O=$(tok odontologo)
Q=00000000-0000-0000-0000-000000000001; S=00000000-0000-0000-0000-000000000002
C1=00000000-0000-0000-0000-0000000000c1; C2=00000000-0000-0000-0000-0000000000c2
B1=00000000-0000-0000-0000-0000000000b1; B2=00000000-0000-0000-0000-0000000000b2; CTRL=00000000-0000-0000-0000-0000000000d4
NX=00000000-0000-0000-0000-00000000ffff
req(){ t="$1"; shift; echo "== $t"; curl -s -o /var/tmp/r.json -w "HTTP %{http_code}\n" "$@"; cat /var/tmp/r.json; echo; }
id(){ python3 -c 'import json;print(json.load(open("/var/tmp/r.json"))["id"])'; }
J='Content-Type: application/json'; L=2026-11-16
req "1 recepcion da turno A1: Quiroga lunes 10:00 Sillon 1 (201)" -X POST $B/appointments -H "Authorization: Bearer $R" -H "$J" -d "{\"patientId\":\"$C1\",\"professionalId\":\"$Q\",\"chairId\":\"$B1\",\"serviceId\":\"$CTRL\",\"startAt\":\"${L}T10:00:00-03:00\"}"; A1=$(id)
req "2 recepcion da turno A2: Sosa lunes 09:00 Sillon 2 (201)" -X POST $B/appointments -H "Authorization: Bearer $R" -H "$J" -d "{\"patientId\":\"$C2\",\"professionalId\":\"$S\",\"chairId\":\"$B2\",\"serviceId\":\"$CTRL\",\"startAt\":\"${L}T09:00:00-03:00\"}"; A2=$(id)
req "3 odontologo (Quiroga) confirma A1, turno propio (200)" -X POST $B/appointments/$A1/status -H "Authorization: Bearer $O" -H "$J" -d '{"toStatus":"confirmado"}'
req "4 confirmar A1 otra vez: mismo estado (422 INVALID_TRANSITION)" -X POST $B/appointments/$A1/status -H "Authorization: Bearer $R" -H "$J" -d '{"toStatus":"confirmado"}'
req "5 odontologo (Quiroga) confirma A2 de Sosa (403 del dominio)" -X POST $B/appointments/$A2/status -H "Authorization: Bearer $O" -H "$J" -d '{"toStatus":"confirmado"}'
req "6 /status con cancelado (400)" -X POST $B/appointments/$A1/status -H "Authorization: Bearer $R" -H "$J" -d '{"toStatus":"cancelado"}'
req "7 marcar atendido A1 antes de su hora (422 STATUS_CHANGE_TOO_EARLY)" -X POST $B/appointments/$A1/status -H "Authorization: Bearer $R" -H "$J" -d '{"toStatus":"atendido"}'
req "8 reprogramar A1 a las 11:00, solo startAt (200, vuelve a reservado)" -X POST $B/appointments/$A1/reschedule -H "Authorization: Bearer $R" -H "$J" -d "{\"startAt\":\"${L}T11:00:00-03:00\"}"
req "9 reprogramar A2 a las 11:00 en Sillon 1 (409 CHAIR_OVERLAP)" -X POST $B/appointments/$A2/reschedule -H "Authorization: Bearer $R" -H "$J" -d "{\"startAt\":\"${L}T11:00:00-03:00\",\"chairId\":\"$B1\"}"
req "10 reprogramar A2 al pasado (422 IN_THE_PAST)" -X POST $B/appointments/$A2/reschedule -H "Authorization: Bearer $R" -H "$J" -d '{"startAt":"2026-11-02T10:00:00-03:00"}'
req "11 reprogramar sin zona horaria (400)" -X POST $B/appointments/$A2/reschedule -H "Authorization: Bearer $R" -H "$J" -d "{\"startAt\":\"${L}T12:00:00\"}"
req "12 odontologo intenta reprogramar (403)" -X POST $B/appointments/$A1/reschedule -H "Authorization: Bearer $O" -H "$J" -d "{\"startAt\":\"${L}T12:00:00-03:00\"}"
req "13 odontologo intenta cancelar (403)" -X POST $B/appointments/$A1/cancel -H "Authorization: Bearer $O"
req "14 recepcion cancela A2 (200)" -X POST $B/appointments/$A2/cancel -H "Authorization: Bearer $R"
req "15 cancelar A2 otra vez (422 INVALID_TRANSITION)" -X POST $B/appointments/$A2/cancel -H "Authorization: Bearer $R"
req "16 cancelar turno inexistente (404)" -X POST $B/appointments/$NX/cancel -H "Authorization: Bearer $R"
req "17 historial de A1 como recepcion (200: alta, confirmado, reprogramacion)" $B/appointments/$A1/history -H "Authorization: Bearer $R"
req "18 historial de A1 como odontologo, turno propio (200)" $B/appointments/$A1/history -H "Authorization: Bearer $O"
req "19 historial de A2 (Sosa) como odontologo (403)" $B/appointments/$A2/history -H "Authorization: Bearer $O"
req "20 historial de turno inexistente (404)" $B/appointments/$NX/history -H "Authorization: Bearer $R"
echo "== 21 turno A3 de Quiroga ya empezado, insertado en la base (como en los tests de C-23)"
A3=$(python3 -c 'import uuid;print(uuid.uuid4())')
$PSQL -c "insert into appointment values ('$A3','$C1','$Q','$B1','$CTRL', date_trunc('hour', now()) - interval '2 hours', date_trunc('hour', now()) - interval '90 minutes','reservado', now(), now())" -c "select start_at, status from appointment where id='$A3'"
req "22 odontologo marca atendido A3 (200)" -X POST $B/appointments/$A3/status -H "Authorization: Bearer $O" -H "$J" -d '{"toStatus":"atendido"}'
req "23 marcar ausente A3 ya atendido (422 INVALID_TRANSITION)" -X POST $B/appointments/$A3/status -H "Authorization: Bearer $R" -H "$J" -d '{"toStatus":"ausente"}'
echo "== 24 historial completo en la base"
$PSQL -c "select a.id='$A1' as es_a1, coalesce(h.from_status,'-'), h.to_status, u.username, h.reschedule_previous_start_at is not null as con_detalle from appointment_status_change h join appointment a on a.id=h.appointment_id join app_user u on u.id=h.changed_by order by a.start_at, h.changed_at"