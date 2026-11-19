# PolicySearch

Buscador documental para equipos de operaciones y seguridad. Indexa procedimientos locales en Markdown o texto y devuelve fragmentos relevantes con archivo y líneas de origen para que la persona pueda verificar la respuesta.

**Lenguaje:** Python  
**Dependencias:** biblioteca estándar  
**Caso de uso:** localizar políticas internas sin enviar documentos a un servicio externo.

## Ejecutar

~~~bash
cd projects/policy-search
python -m policy_search.cli --docs examples/policies --query "rotate an API key"
~~~

El modo actual es extractivo: muestra pasajes recuperados y sus referencias; no inventa una respuesta ni requiere una clave de modelo. El índice se construye bajo demanda para mantener el uso local y sencillo.
