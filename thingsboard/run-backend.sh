#!/usr/bin/env bash
#
# Copyright © 2016-2025 The Thingsboard Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -euo pipefail

cd /home/zinex/Thingsboard_mine/thingsboard

JAR_PATH="$(ls -1 application/target/thingsboard-*-boot.jar 2>/dev/null | head -n 1 || true)"
if [ -z "${JAR_PATH}" ]; then
  echo "ERROR: Cannot find application/target/thingsboard-*-boot.jar"
  echo "Run: mvn -pl application -am clean install -DskipTests -Dlicense.skip=true"
  exit 1
fi

if ss -ltn 2>/dev/null | grep -q ':8080 '; then
  echo "ERROR: Port 8080 is already in use."
  echo "If Docker is running tb-node, stop it first:"
  echo "  sudo docker compose stop thingsboard-ce"
  exit 1
fi

export LOADER_PATH=application/target/conf,application/target/extensions
export SPRING_CONFIG_ADDITIONAL_LOCATION=application/target/conf/
export TB_SERVICE_ID=tb-local-dev

# Local PostgreSQL defaults (same as your current dev DB setup)
export SPRING_DATASOURCE_URL="${SPRING_DATASOURCE_URL:-jdbc:postgresql://127.0.0.1:5432/hospicare}"
export SPRING_DATASOURCE_USERNAME="${SPRING_DATASOURCE_USERNAME:-postgres}"
export SPRING_DATASOURCE_PASSWORD="${SPRING_DATASOURCE_PASSWORD:-postgres}"
export SPRING_EVENTS_DATASOURCE_URL="${SPRING_EVENTS_DATASOURCE_URL:-jdbc:postgresql://127.0.0.1:5432/hospicare_events}"
export SPRING_EVENTS_DATASOURCE_USERNAME="${SPRING_EVENTS_DATASOURCE_USERNAME:-postgres}"
export SPRING_EVENTS_DATASOURCE_PASSWORD="${SPRING_EVENTS_DATASOURCE_PASSWORD:-postgres}"

# Keep local startup minimal and avoid edge gRPC bind conflicts.
export EDGES_ENABLED=false
export EDGES_RPC_PORT=7071
export MQTT_ENABLED=false
export COAP_ENABLED=false
export LWM2M_ENABLED=false
export SNMP_ENABLED=false

exec java -jar "${JAR_PATH}"
