{{- define "smart-remedy.backendFullname" -}}
{{- printf "%s" .Values.backend.name -}}
{{- end -}}

{{- define "smart-remedy.frontendFullname" -}}
{{- printf "%s" .Values.frontend.name -}}
{{- end -}}

{{- define "smart-remedy.backendServiceFQDN" -}}
{{- printf "%s.%s.svc.cluster.local" .Values.backend.service.name .Values.backend.namespace -}}
{{- end -}}

