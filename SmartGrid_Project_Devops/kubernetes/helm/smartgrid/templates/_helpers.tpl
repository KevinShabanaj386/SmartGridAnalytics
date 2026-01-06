{{/*
Common labels
*/}}
{{- define "smartgrid.labels" -}}
app: {{ .Values.services.apiGateway.name | default "smartgrid" }}
chart: {{ .Chart.Name }}-{{ .Chart.Version }}
release: {{ .Release.Name }}
{{- end }}

{{/*
Common selector labels
*/}}
{{- define "smartgrid.selectorLabels" -}}
app: {{ .Values.services.apiGateway.name | default "smartgrid" }}
release: {{ .Release.Name }}
{{- end }}
