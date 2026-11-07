B=${API_URL:-http://localhost:8000/api}; P="$SEED_USER_PASSWORD"
tok(){ curl -s -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$P\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["accessToken"])'; }
R=$(tok recepcion); O=$(tok odontologo)
Q=00000000-0000-0000-0000-000000000001; S=00000000-0000-0000-0000-000000000002
C1=00000000-0000-0000-0000-0000000000c1; C2=00000000-0000-0000-0000-0000000000c2; C3=00000000-0000-0000-0000-0000000000c3
B1=00000000-0000-0000-0000-0000000000b1; B2=00000000-0000-0000-0000-0000000000b2
CTRL=00000000-0000-0000-0000-0000000000d4; EXT=00000000-0000-0000-0000-0000000000d2
post(){ echo "== $1"; shift; curl -s -o /var/tmp/r.json -w "HTTP %{http_code}\n" -X POST "$@"; cat /var/tmp/r.json; echo; }
body(){ echo "{\"patientId\":\"$1\",\"professionalId\":\"$2\",\"chairId\":\"$3\",\"serviceId\":\"$4\",\"startAt\":\"$5\"$6}"; }
L=2026-11-16
post "1 recepcion da turno Quiroga lunes 10:00 Control (201)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C1 $Q $B1 $CTRL ${L}T10:00:00-03:00)"
post "2 choque de profesional 10:15 otro sillon (409)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL ${L}T10:15:00-03:00)"
post "3 choque de sillon con Sosa 10:00 sillon 1 (409)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $S $B1 $CTRL ${L}T10:00:00-03:00)"
post "4 turno en el pasado (422)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL 2026-11-02T10:00:00-03:00)"
post "5 fuera de horario 14:00 (409)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL ${L}T14:00:00-03:00)"
post "6 startAt sin zona (400)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL ${L}T15:00:00)"
post "7 paciente inexistente (422)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body 00000000-0000-0000-0000-0000000000c9 $Q $B2 $CTRL ${L}T15:00:00-03:00)"
post "8 odontologo intenta dar turno (403)" $B/appointments -H "Authorization: Bearer $O" -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL ${L}T15:00:00-03:00)"
post "9 sin token (401)" $B/appointments -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL ${L}T15:00:00-03:00)"
post "10a odontologo bloquea 11:00-12:00 (201)" $B/professionals/$Q/blocks -H "Authorization: Bearer $O" -H 'Content-Type: application/json' -d "{\"startAt\":\"${L}T11:00:00-03:00\",\"endAt\":\"${L}T12:00:00-03:00\",\"reason\":\"Prueba\"}"
post "10b turno dentro del bloqueo (409)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $Q $B2 $CTRL ${L}T11:00:00-03:00)"
post "11 Extraccion sin durationMin: dura 60 min (201)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C3 $Q $B2 $EXT ${L}T15:00:00-03:00)"
post "12 durationMin 45 explicito (201)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $S $B2 $CTRL ${L}T09:00:00-03:00 ,\"durationMin\":45)"
post "13 campo extra status (400)" $B/appointments -H "Authorization: Bearer $R" -H 'Content-Type: application/json' -d "$(body $C2 $S $B2 $CTRL ${L}T12:00:00-03:00 ,\"status\":\"confirmado\")"
echo "== 14 historial en la base"
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "select a.start_at, a.status, h.from_status, h.to_status, u.username from appointment a join appointment_status_change h on h.appointment_id=a.id join app_user u on u.id=h.changed_by order by a.start_at"