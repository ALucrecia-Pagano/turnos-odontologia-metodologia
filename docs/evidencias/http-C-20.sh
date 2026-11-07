B=${API_URL:-http://localhost:8000/api}; P="$SEED_USER_PASSWORD"
tok(){ curl -s -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$P\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["accessToken"])'; }
R=$(tok recepcion); O=$(tok odontologo); A=$(tok administrador)
NX=00000000-0000-0000-0000-00000000ffff; J='Content-Type: application/json'
req(){ t="$1"; shift; echo "== $t"; curl -s -o /var/tmp/r.json -w "HTTP %{http_code}\n" "$@"; python3 -c 'import json;d=json.load(open("/var/tmp/r.json"));print(" ",json.dumps(d,ensure_ascii=False)[:330])'; }
id(){ python3 -c 'import json;print(json.load(open("/var/tmp/r.json"))["id"])'; }
req "1 recepcion lista profesionales (200)" $B/professionals -H "Authorization: Bearer $R"
req "2 odontologo lista sillones (200)" $B/chairs -H "Authorization: Bearer $O"
req "3 odontologo lista prestaciones (200)" $B/services -H "Authorization: Bearer $O"
req "4 admin crea profesional Dr. Ficticio Nuevo (201)" -X POST $B/professionals -H "Authorization: Bearer $A" -H "$J" -d '{"fullName":"Dr. Ficticio Nuevo","licenseNumber":"MP-9999"}'; PN=$(id)
req "5 recepcion intenta crear profesional (403)" -X POST $B/professionals -H "Authorization: Bearer $R" -H "$J" -d '{"fullName":"Dr. Otro"}'
req "6 admin edita el profesional (200)" -X PUT $B/professionals/$PN -H "Authorization: Bearer $A" -H "$J" -d '{"fullName":"Dr. Ficticio Editado","licenseNumber":"MP-9999"}'
req "7 admin desactiva el profesional (200, active false)" -X POST $B/professionals/$PN/deactivate -H "Authorization: Bearer $A"
req "8 admin reactiva el profesional (200, active true)" -X POST $B/professionals/$PN/reactivate -H "Authorization: Bearer $A"
req "9 profesional inexistente (404)" $B/professionals/$NX -H "Authorization: Bearer $R"
req "10 admin crea Sillon 4 (201)" -X POST $B/chairs -H "Authorization: Bearer $A" -H "$J" -d '{"name":"Sillón 4"}'
req "11 sillon con nombre repetido, otras mayusculas (409 DUPLICATE_NAME)" -X POST $B/chairs -H "Authorization: Bearer $A" -H "$J" -d '{"name":"  sillón 4 "}'
req "12 admin crea prestacion Sellado ficticio 45 min (201)" -X POST $B/services -H "Authorization: Bearer $A" -H "$J" -d '{"name":"Sellado ficticio","defaultDurationMin":45}'
req "12b prestacion repetida Blanqueamiento, ya existe en el seed (409 DUPLICATE_NAME)" -X POST $B/services -H "Authorization: Bearer $A" -H "$J" -d '{"name":"Blanqueamiento","defaultDurationMin":45}'
req "13 prestacion con duracion 0 (422)" -X POST $B/services -H "Authorization: Bearer $A" -H "$J" -d '{"name":"Prueba","defaultDurationMin":0}'
req "14 recepcion crea paciente ficticio (201)" -X POST $B/patients -H "Authorization: Bearer $R" -H "$J" -d '{"fullName":"Paciente Ficticio","dni":"40111222","phone":"261-0000000"}'; PA=$(id)
req "15 paciente con DNI repetido (409 DUPLICATE_DNI)" -X POST $B/patients -H "Authorization: Bearer $R" -H "$J" -d '{"fullName":"Otro Paciente","dni":"40111222"}'
req "16 paciente con DNI de 6 digitos (422)" -X POST $B/patients -H "Authorization: Bearer $R" -H "$J" -d '{"fullName":"Otro Paciente","dni":"123456"}'
req "17 odontologo intenta crear paciente (403)" -X POST $B/patients -H "Authorization: Bearer $O" -H "$J" -d '{"fullName":"Otro Paciente","dni":"40999888"}'
req "18 buscar paciente por nombre 'pérez' (200)" "$B/patients?query=p%C3%A9rez" -H "Authorization: Bearer $R"
req "19 buscar paciente por prefijo de DNI '401' (200)" "$B/patients?query=401" -H "Authorization: Bearer $R"
req "20 recepcion edita el telefono del paciente (200)" -X PUT $B/patients/$PA -H "Authorization: Bearer $R" -H "$J" -d '{"fullName":"Paciente Ficticio","dni":"40111222","phone":"261-1111111"}'
req "21 campo extra en el paciente (400)" -X POST $B/patients -H "Authorization: Bearer $R" -H "$J" -d '{"fullName":"X","dni":"40999777","historiaClinica":"no"}'
req "22 sin token (401)" $B/patients