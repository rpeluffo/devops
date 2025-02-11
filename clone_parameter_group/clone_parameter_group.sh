#!/bin/bash

# Define Variables
ParameterGroup="param-datahub-be-cover-group-postgres1420250108084849537300000002"
NewPgName="param-datahub-be-cover-group-postgres14-rpeluffo"

# Fetch the existing parameter group settings and save to a JSON file
aws rds describe-db-parameters --db-parameter-group-name "$ParameterGroup" --query "Parameters" --output json > parameters.json

# List of parameters to exclude
EXCLUDED_PARAMS='["archive_command", "archive_timeout", "config_file", "cron.use_background_workers", "data_directory", "fsync","full_page_writes", 
"hba_file", "ident_file", "ignore_invalid_pages", "lo_compat_privileges", "listen_addresses", "log_directory", "log_file_mode", "log_line_prefix", 
"log_timezone", "log_truncate_on_rotation", "logging_collector", "pgactive.max_nodes", "port", "rds.max_tcp_buffers", "rds.rds_reserved_connections", 
"recovery_init_sync_method", "ssl", "ssl_ca_file", "ssl_cert_file", "ssl_key_file", "superuser_reserved_connections", "unix_socket_directories", 
"unix_socket_permissions", "recovery_init_sync_method", "stats_temp_directory", "unix_socket_group", "update_process_title", "wal_receiver_create_temp_slot"]'

# Remove unmodifiable parameters and those containing invalid function values
jq '
    [.[] |
    select(.ParameterValue != null and (.ParameterValue | test("\\$\\{.*\\}") | not) and (.ParameterValue | test("\\{.*\\}") | not) ) | 
    {ParameterName, ParameterValue, ApplyMethod: "pending-reboot"}
    ] | unique_by(.ParameterName)' parameters.json > filtered_parameters.json

jq --argjson exclude "$EXCLUDED_PARAMS" '
[
        .[] | select(.ParameterName | IN($exclude[]) | not) |
        {ParameterName, ParameterValue, ApplyMethod: "pending-reboot"}
    ]
' filtered_parameters.json > final_parameters.json

# Get total number of parameters
total_params=$(jq length final_parameters.json)
chunk_size=20
num_chunks=$(( (total_params + chunk_size - 1) / chunk_size ))

echo "Total parameters after filtering and deduplication: $total_params"
echo "Processing in $num_chunks chunks..."

# Process chunks
for (( i=0; i<num_chunks; i++ )); do
    chunk_file="chunk_$i.json"

    # Extract a chunk of 20 unique parameters and save to a file
    jq ".[$((i*chunk_size)):$(( (i+1)*chunk_size ))]" final_parameters.json > "$chunk_file"

    # Create full JSON structure required for AWS CLI
    cat > cli_input.json <<EOF
{
    "DBParameterGroupName": "$NewPgName",
    "Parameters": $(cat "$chunk_file")
}
EOF

    echo "Applying chunk $((i+1))/$num_chunks using cli_input.json..."

    # Apply the chunk using --cli-input-json
    aws rds modify-db-parameter-group --cli-input-json file://cli_input.json

    # Remove temporary files after processing
    rm -f "$chunk_file" cli_input.json filtered_parameters.json
done

echo "All parameters applied successfully!"






# ParameterGroup="param-datahub-be-cover-group-postgres1420250108084849537300000002"
# aws rds describe-db-parameters --db-parameter-group-name $ParameterGroup --query "Parameters" --output json > parameters.json
# PG_Family="postgres14"
# TAGS="Key=Owner,Value=datahub_devops@eulerhermes.com Key=app.service,Value=EV_datahub_busevent_TRADE_D Key=Application,Value=datahub_be_cover_group"
# NewPgName="param-datahub-be-cover-group-postgres14-rpeluffo"
# #aws rds create-db-parameter-group --db-parameter-group-name $NewPgName --db-parameter-group-family $PG_Family \
# # --description "Cloned from $ParameterGroup" --tags $TAGS

# # Get the parameters into an array (filter out null values)
# params=$(jq -r '.[] | select(.ParameterValue != null) | {ParameterName, ParameterValue, ApplyMethod}' parameters.json)
# echo $params | jq
# # Create an array to hold chunks of 20 parameters
# chunk_size=20
# count=0
# chunk=()

# # Loop through the parameters and chunk them
# for param in $(echo "$params" | jq -r '. | @base64'); do
#     # Decode each parameter
#     _jq() {
#         echo ${param} | base64 --decode | jq -r ${1}
#     }

#     # Add parameter to the current chunk
#     chunk+=(
#         "ParameterName=$(_jq '.ParameterName')"
#         "ParameterValue=$(_jq '.ParameterValue')"
#         "ApplyMethod=pending-reboot"
#     )

#     # If chunk size reaches 20, send the chunk
#     if [[ ${#chunk[@]} -ge $chunk_size ]]; then
#         # Send the chunk in one request
#         aws rds modify-db-parameter-group --db-parameter-group-name $NewPgName --parameters "${chunk[@]}"
        
#         # Reset chunk
#         chunk=()
#     fi
# done

# # If there are remaining parameters in the chunk, apply them
# if [[ ${#chunk[@]} -gt 0 ]]; then
#     aws rds modify-db-parameter-group --db-parameter-group-name $NewPgName --parameters "${chunk[@]}"
# fi