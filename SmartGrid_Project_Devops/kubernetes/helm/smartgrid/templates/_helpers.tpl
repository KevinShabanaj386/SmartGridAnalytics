{{/*
Common labels
*/}}
{{- define "smartgrid.labels" -}}
app: smartgrid
chart: {{ .Chart.Name }}-{{ .Chart.Version }}
release: {{ .Release.Name }}
{{- end }}

{{/*
Common selector labels
*/}}
{{- define "smartgrid.selectorLabels" -}}
app: smartgrid
release: {{ .Release.Name }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "smartgrid.namespace" -}}
{{- .Values.namespace | default "smartgrid" }}
{{- end }}
