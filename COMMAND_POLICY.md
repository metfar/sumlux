# Σlux — Contrato de verdad y ejecución de comandos

Fecha: 2026-09-22. Estado: especificación futura, NO implementado en 0.1.0a5.

## Estado actual

Σlux 0.1.0a5 **no ejecuta comandos solicitados por el modelo ni por el chat**, no inspecciona hardware ni modifica privilegios. `suminfo` solo puede analizarse si la persona pega su salida real. El adaptador del modelo no posee herramientas ni mecanismo de llamadas al sistema. Se agregan advertencias y filtros defensivos, pero un filtro textual no constituye una garantía general de veracidad del LLM. Nunca atribuirle hechos verificables que no se hayan obtenido de una fuente comprobable.

## Reglas vinculantes para una implementación posterior

1. El modelo propone una acción estructurada; jamás puede escribir directamente a shell ni derivar comandos de texto de conversación sin pasar por el ejecutor.
2. El ejecutor determina el binario REAL y argumentos y los valida con una allowlist mínima de acciones consultivas previamente auditadas. No aceptar `shell=True`, `sh -c`, redirecciones, tuberías, globbing, sustituciones, argumentos arbitrarios ni programas no auditados. `suminfo` requiere auditoría de su contenido exacto y procedencia antes de incluirlo.
3. Rechazar toda operación con posible destrucción o escritura de datos, cambios de privilegio, usuarios, grupos, ACL, permisos, capacidades, sudo/su/doas/pkexec, modificaciones de servicios, procesos, paquetes, red, archivos o configuración. **Una confirmación no convierte un comando rechazado en permitido.**
4. Para cada operación individual que pasó validación: mostrar binario absoluto, argumentos, propósito, efectos declarados, directorio de ejecución, usuario efectivo e información que saldrá de la máquina. Requerir confirmación explícita nueva, no recordada, antes de lanzar el proceso. Cancelar/no confirmar = no ejecutar.
5. Sin elevación de privilegios; sin credenciales; límite de ejecución, salida y recursos; sin heredar secretos arbitrarios desde entorno; proceso separado y abortable. Registrar consentimiento, comando exacto, fecha, código de salida, stdout/stderr y fuente local con trazabilidad. No asumir que `exit 0` valida la veracidad de los datos.
6. Si no puede demostrarse ausencia de efectos destructivos o de escalada de privilegio, no ejecutar. En caso de salida vacía, error, timeout o cancelación, no presentar datos como observados.

**Límite práctico:** inspección estática de una línea de comando NO prueba que un ejecutable externo sea inocuo. Para 100 % seguridad técnica hacen falta verificación del binario y aislamiento a nivel del sistema operativo, y aun así se deben documentar las garantías y excepciones reales.
