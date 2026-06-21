
const AV_CHATBOT = (function () {

    // ── 🔑 KEYS CARGADAS DESDE keys.js ──
    const GROQ_KEYS = typeof GROQ_KEYS_LOCAL !== 'undefined' ? GROQ_KEYS_LOCAL : [];
    const GROQ_URL  = 'https://api.groq.com/openai/v1/chat/completions';
    const STORAGE_PREFIX = 'av-chat-';
    const MAX_HISTORY    = 10; // últimos mensajes para contexto
    const MAX_SAVED_MSGS = 50; // máximos mensajes guardados en localStorage

    // ── Estado ──
    let groqKeyIndex = 0;
    let usuario      = null;
    let systemPrompt = '';
    let convHistory  = []; // {role, content} para Groq
    let abierto      = false;

    // ═══════════════════════════════════════════════════════
    //  USUARIO — validación contra backend
    // ═══════════════════════════════════════════════════════
    async function initUsuario() {
        try {
            if (typeof USUARIO !== 'undefined' && USUARIO && USUARIO.id_usuario) {
                const resp = await fetch('/api/usuario/me');
                if (!resp.ok) return USUARIO;
                const data = await resp.json();
                if (!data.ok) return USUARIO;
                return data.usuario;
            }
            return null;
        } catch (e) {
            return typeof USUARIO !== 'undefined' ? USUARIO : null;
        }
    }

    // ═══════════════════════════════════════════════════════
    //  SYSTEM PROMPT — construido UNA vez al iniciar
    // ═══════════════════════════════════════════════════════
    function buildSystemPrompt(u) {
        const rol    = u.rol_nombre;
        const nombre = u.nombre_completo;

        const base = 'Eres AgroBot, el asistente virtual de AGROVISION, un sistema de gestión empresarial peruano.\n'
                   + 'Responde siempre en español, de forma amigable, clara y concisa. Máximo 4 líneas por respuesta.\n'
                   + 'Usa emojis con moderación. Usa etiquetas HTML <strong> para resaltar términos importantes.\n'
                   + 'El usuario se llama ' + nombre + ' y tiene rol: ' + rol + '.\n'
                   + 'IMPORTANTE: Solo responde preguntas relacionadas con AGROVISION. Si preguntan otra cosa, redirige amablemente.\n'
                   + 'Si el usuario pregunta algo que su rol NO puede hacer, explícale claramente que no tiene acceso y qué sí puede hacer.\n'
                   + 'No menciones que eres una IA de Groq o Meta. Eres AgroBot de AGROVISION.';

        const contextos = {
            admin:       '\nROL ADMIN — acceso total: Puede: Dashboard, todos los tickets, resolver tickets, aplicaciones, nuevo proyecto, ver proyectos, aprobación de proyectos, nueva actividad, indicadores KPI, lista de usuarios, reportes Excel.',
            programador: '\nROL PROGRAMADOR — acceso parcial: Puede: Dashboard, crear ticket, ver sus tickets, resolver tickets asignados, ver proyectos donde participa, nueva actividad. NO puede: Crear/aprobar proyectos, aplicaciones, indicadores, reportes, lista de usuarios.',
            soporte:     '\nROL SOPORTE — acceso básico: Puede: Dashboard, crear tickets, ver sus tickets, calificar tickets resueltos, cancelar sus tickets. NO puede: Resolver tickets, proyectos, actividades, aplicaciones, indicadores, reportes, usuarios.',
            agente:      '\nROL AGENTE — solo tickets asignados: Puede: Ver tickets asignados, resolver tickets asignados. NO puede: Proyectos, actividades, aplicaciones, indicadores, reportes, usuarios.'
        };

        return base + (contextos[rol] || contextos.soporte);
    }

    // ═══════════════════════════════════════════════════════
    //  HISTORIAL PERSISTIDO
    // ═══════════════════════════════════════════════════════
    function storageKey() {
        return STORAGE_PREFIX + (usuario ? usuario.id_usuario : 'anon');
    }

    function loadHistory() {
        try {
            const saved = localStorage.getItem(storageKey());
            if (saved) {
                const parsed = JSON.parse(saved);
                convHistory = parsed.conv || [];
                return parsed.msgs || [];
            }
        } catch {}
        return [];
    }

    function saveHistory(displayMsgs) {
        try {
            localStorage.setItem(storageKey(), JSON.stringify({
                conv: convHistory.slice(-MAX_HISTORY),
                msgs: displayMsgs.slice(-MAX_SAVED_MSGS)
            }));
        } catch {}
    }

    // ═══════════════════════════════════════════════════════
    //  FAQ HARDCODEADO
    // ═══════════════════════════════════════════════════════
    const FAQ_GENERAL = [
        {
            patrones: ['que es agrovision', 'para que sirve', 'de que trata', 'que hace agrovision'],
            respuesta: '🌿 <strong>AGROVISION</strong> es un sistema de gestión empresarial que centraliza:\n\n• 🎫 <strong>Soporte</strong>: Tickets de incidencias y peticiones\n• 🚀 <strong>Proyectos</strong>: Gestión ágil con sprints y actividades\n• 📊 <strong>Indicadores y reportes</strong> en tiempo real\n\n¿Sobre qué parte quieres saber más?'
        },
        {
            patrones: ['cerrar sesion', 'salir', 'logout', 'como salgo', 'como cierro sesion'],
            respuesta: '🚪 Para cerrar sesión haz clic en el botón <strong>"Salir"</strong> que está arriba a la derecha en la barra verde.'
        },
        {
            patrones: ['perfil', 'mi perfil', 'editar perfil', 'mis datos', 'cambiar foto'],
            respuesta: '👤 Tu perfil está disponible desde el menú lateral. Ahí puedes ver tus datos y estadísticas de participación.'
        },
        {
            patrones: ['contrasena', 'password', 'olvide', 'cambiar clave', 'recuperar contrasena'],
            respuesta: '🔑 Si olvidaste tu contraseña, en la pantalla de login haz clic en <strong>"¿Olvidaste tu contraseña?"</strong> e ingresa tu correo registrado.'
        },
        {
            patrones: ['hola', 'buenas', 'buenos dias', 'buenas tardes', 'buenas noches', 'hey', 'saludos', 'hi'],
            respuesta: null
        }
    ];

    const FAQ_POR_ROL = {
        Soporte: [
            {
                patrones: ['nuevo ticket', 'crear ticket', 'abrir ticket', 'registrar ticket', 'como creo un ticket', 'como abro un ticket', 'quiero crear un ticket', 'quiero abrir un ticket'],
                respuesta: '🎫 Para crear un ticket:\n\n1. Clic en <strong>"Nuevo ticket"</strong> en el menú lateral\n2. Escribe un <strong>título claro</strong> del problema\n3. Selecciona el <strong>tipo</strong>: Incidencia 🔴, Petición 🔵 o Consulta 🟡\n4. Elige la <strong>aplicación afectada</strong>\n5. Describe el problema con detalle\n6. Clic en <strong>"Enviar ticket"</strong> 📨'
            },
            {
                patrones: ['ver tickets', 'mis tickets', 'estado ticket', 'estados del ticket', 'listar tickets', 'donde veo mis tickets'],
                respuesta: '📨 Ve a <strong>"Ver tickets"</strong> en el menú lateral.\n\nEstados posibles:\n• <strong>Solicitado</strong> → Esperando asignación\n• <strong>En progreso</strong> → Siendo atendido\n• <strong>Resuelto</strong> → El agente lo solucionó\n• <strong>Cerrado</strong> → Confirmado y cerrado\n• <strong>Cancelado</strong> → Anulado'
            },
            {
                patrones: ['tipo ticket', 'tipos de ticket', 'que tipos', 'incidencia', 'peticion', 'consulta', 'diferencia entre'],
                respuesta: '📋 Los tipos de ticket son:\n\n🔴 <strong>Incidencia</strong>: Algo que no funciona, un error o falla\n🔵 <strong>Petición</strong>: Solicitud de acceso o cuenta nueva\n🟡 <strong>Consulta</strong>: Pregunta o duda sobre el sistema'
            },
            {
                patrones: ['calificar', 'calificacion', 'estrellas', 'valorar', 'puntuar', 'como califico'],
                respuesta: '⭐ Puedes calificar un ticket cuando su estado sea <strong>"Resuelto"</strong>. En la lista de tickets verás el botón de calificación.'
            },
            {
                patrones: ['cancelar ticket', 'anular ticket', 'eliminar ticket', 'borrar ticket', 'como cancelo'],
                respuesta: '❌ Puedes cancelar un ticket propio siempre que aún no esté cerrado. Ingresa al ticket y busca la opción de cancelar.'
            },
            {
                patrones: ['prioridad', 'urgente', 'critico', 'urgencia', 'que significa prioridad'],
                respuesta: '⚡ La prioridad la asigna el agente:\n\n🚨 <strong>Crítica</strong>: Sistema caído\n🔴 <strong>Alta</strong>: Afecta a varios usuarios\n🟡 <strong>Media</strong>: Impacto moderado\n⚪ <strong>Baja</strong>: Puede esperar'
            },
            {
                patrones: ['resolver ticket', 'resuelvo', 'solucionar ticket', 'atender ticket', 'como resuelvo'],
                respuesta: '🚫 Como <strong>soporte</strong> no puedes resolver tickets, eso lo hace el agente asignado.\n\nTu rol es <strong>crear tickets</strong> y hacer seguimiento. Cuando el agente lo resuelva podrás <strong>calificarlo</strong> ⭐'
            },
            {
                patrones: ['ver proyectos', 'crear proyecto', 'nuevo proyecto', 'acceder proyectos', 'donde estan proyectos'],
                respuesta: '🚫 Como <strong>soporte</strong> no tienes acceso a proyectos. Esa sección es para programadores y administradores.\n\nTu área es el <strong>módulo de tickets</strong> 🎫'
            },
            {
                patrones: ['indicadores', 'reportes', 'kpi', 'metricas', 'estadisticas', 'ver indicadores'],
                respuesta: '🚫 Como <strong>soporte</strong> no tienes acceso a indicadores ni reportes. Esa sección es exclusiva del administrador.'
            },
            {
                patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'],
                respuesta: null
            }
        ],
        Programador: [
            {
                patrones: ['resolver ticket', 'resuelvo', 'como resuelvo', 'atender ticket', 'solucionar ticket', 'resolver un ticket', 'como resuelvo un ticket'],
                respuesta: '🔧 Para resolver un ticket:\n\n1. Ve a <strong>"Resolver tickets"</strong> en el menú lateral\n2. Verás los tickets asignados a ti\n3. Haz clic en <strong>"Resolver"</strong>\n4. Completa la descripción de la solución\n5. Guarda para marcarlo como resuelto\n\nSolo puedes resolver tickets que te hayan asignado.'
            },
            {
                patrones: ['ver proyectos', 'mis proyectos', 'listar proyectos', 'donde veo proyectos', 'como veo proyectos'],
                respuesta: '📁 Ve a <strong>"Ver proyectos"</strong> en el menú. Verás los proyectos en los que participas:\n\n• En revisión → Esperando aprobación\n• Planificado → Aprobado\n• En desarrollo → En curso\n• QA → En pruebas\n• Completado → Finalizado'
            },
            {
                patrones: ['sprint', 'sprints', 'que es un sprint', 'que son los sprints', 'para que sirve un sprint'],
                respuesta: '🏃 Un <strong>sprint</strong> es un período de trabajo corto (1-2 semanas) donde el equipo completa un conjunto de actividades.\n\nCada proyecto tiene sprints y dentro de cada uno se registran las <strong>actividades</strong> con story points.'
            },
            {
                patrones: ['nueva actividad', 'crear actividad', 'registrar actividad', 'como creo una actividad', 'quiero crear una actividad', 'agregar actividad'],
                respuesta: '📋 Para crear una actividad:\n\n1. Clic en <strong>"Nueva actividad"</strong> en el menú\n2. El código se genera automáticamente\n3. Escribe el título\n4. Selecciona el <strong>proyecto</strong> y el <strong>sprint</strong>\n5. Asigna responsable, prioridad y story points\n6. Guarda'
            },
            {
                patrones: ['story points', 'puntos historia', 'estimacion', 'esfuerzo', 'que son story points'],
                respuesta: '📊 Los <strong>story points</strong> representan el esfuerzo estimado de una actividad. No son horas exactas, sino una medida relativa del equipo.'
            },
            {
                patrones: ['avance proyecto', 'avances', 'registrar avance', 'progreso proyecto', 'como registro avance'],
                respuesta: '📈 Ve a <strong>"Ver proyectos"</strong>, selecciona el proyecto y encontrarás la opción para registrar avances con porcentaje de progreso.'
            },
            {
                patrones: ['nuevo proyecto', 'crear proyecto', 'registrar proyecto', 'como creo un proyecto', 'como creo', 'quiero crear proyecto'],
                respuesta: '🚫 Como <strong>programador</strong> no puedes crear proyectos. Solo el <strong>administrador</strong> puede crearlos y aprobarlos.\n\nTú puedes ver los proyectos donde participas desde <strong>📁 Ver proyectos</strong>.'
            },
            {
                patrones: ['aprobar proyecto', 'aprobacion proyecto', 'rechazar proyecto', 'como apruebo'],
                respuesta: '🚫 Como <strong>programador</strong> no tienes acceso a la aprobación de proyectos. Eso es exclusivo del <strong>administrador</strong>.'
            },
            {
                patrones: ['indicadores', 'reportes', 'kpi', 'metricas', 'estadisticas', 'ver indicadores'],
                respuesta: '🚫 Como <strong>programador</strong> no tienes acceso a indicadores ni reportes. Esa sección es exclusiva del <strong>administrador</strong>.'
            },
            {
                patrones: ['lista usuarios', 'gestionar usuarios', 'ver usuarios', 'administrar usuarios'],
                respuesta: '🚫 Como <strong>programador</strong> no tienes acceso a la lista de usuarios. Esa sección es exclusiva del <strong>administrador</strong>.'
            },
            {
                patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'],
                respuesta: null
            }
        ],
        Admin: [
            {
                patrones: ['aprobar proyecto', 'aprobacion proyecto', 'rechazar proyecto', 'como apruebo', 'revisar proyectos', 'aprobar proyectos'],
                respuesta: '✅ Para aprobar o rechazar proyectos:\n\n1. Ve a <strong>"Aprobación de proyectos"</strong> en el menú\n2. Verás los proyectos con estado <strong>"En revisión"</strong>\n3. Elige <strong>Aprobar</strong> ✅ o <strong>Rechazar</strong> ❌\n4. Al aprobar se generan automáticamente los sprints'
            },
            {
                patrones: ['nuevo proyecto', 'crear proyecto', 'registrar proyecto', 'como creo un proyecto', 'como creo', 'quiero crear proyecto', 'abrir proyecto'],
                respuesta: '🚀 Para crear un proyecto:\n\n1. Clic en <strong>"Nuevo proyecto"</strong> en el menú\n2. Escribe el nombre del proyecto\n3. Selecciona los <strong>Stakeholders</strong>\n4. Fecha de fin planificada\n5. Describe la problemática y solución\n\nEl proyecto se crea en estado <strong>"En revisión"</strong> hasta que lo apruebes.'
            },
            {
                patrones: ['ver proyectos', 'listar proyectos', 'todos los proyectos', 'donde veo proyectos'],
                respuesta: '📁 Ve a <strong>"Ver proyectos"</strong> en el menú lateral. Verás todos los proyectos del sistema con su estado actual.'
            },
            {
                patrones: ['gestionar usuarios', 'lista usuarios', 'ver usuarios', 'buscar usuario', 'administrar usuarios'],
                respuesta: '👥 Ve a <strong>"Lista de Usuarios"</strong> en el menú. Puedes buscar por nombre y ver el perfil completo con estadísticas e historial de cada usuario.'
            },
            {
                patrones: ['indicadores', 'kpi', 'metricas', 'estadisticas', 'ver indicadores', 'que indicadores'],
                respuesta: '📊 Los <strong>indicadores</strong> están en el menú lateral. Incluyen:\n\n• KPIs de tickets por aplicación, prioridad y agente\n• Satisfacción de usuarios\n• Velocidad por sprint\n• Carga de programadores\n• Estado y salud de proyectos\n• SLA por agente'
            },
            {
                patrones: ['reportes', 'reporte', 'informe', 'exportar', 'excel', 'generar reporte', 'como genero reportes'],
                respuesta: '📈 Ve a <strong>"Reportes"</strong> en el menú. Puedes generar y exportar a <strong>Excel</strong>:\n\n• Tickets por aplicación, tipo y estado\n• Story points por programador\n• Rendimiento por sprint\n• Proyectos en riesgo\n• SLA por aplicación\n• Tendencia por mes'
            },
            {
                patrones: ['aplicaciones', 'gestionar aplicaciones', 'nueva aplicacion', 'ver aplicaciones', 'administrar apps'],
                respuesta: '📦 En <strong>"Aplicaciones"</strong> puedes:\n\n• Ver todas las aplicaciones\n• Crear nuevas\n• Editar nombre, peso y descripción\n• Activar o desactivar aplicaciones\n\nLas aplicaciones se asocian a los tickets de soporte.'
            },
            {
                patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'],
                respuesta: null
            }
        ],
        Agente: [
            {
                patrones: ['mis tickets', 'tickets asignados', 'ver mis tickets', 'donde veo mis tickets', 'como veo mis tickets'],
                respuesta: '📨 Ve a <strong>"Ver tickets"</strong> en el menú. Solo verás los tickets asignados a ti. Filtra por estado para ver los que están en progreso.'
            },
            {
                patrones: ['resolver ticket', 'resuelvo', 'como resuelvo', 'solucionar', 'atender', 'como resuelvo un ticket'],
                respuesta: '🔧 Para resolver un ticket:\n\n1. Ve a <strong>"Resolver tickets"</strong> en el menú\n2. Haz clic en <strong>"Resolver"</strong>\n3. Llena la descripción de la solución\n4. Guarda → queda como <strong>Resuelto</strong>'
            },
            {
                patrones: ['ver proyectos', 'crear proyecto', 'indicadores', 'reportes', 'lista usuarios'],
                respuesta: '🚫 Como <strong>agente</strong> tu acceso está limitado a los tickets asignados a ti. No tienes acceso a proyectos, indicadores ni reportes.'
            },
            {
                patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'],
                respuesta: null
            }
        ]
    };

    // ═══════════════════════════════════════════════════════
    //  TUTORIALES POR ROL
    // ═══════════════════════════════════════════════════════
    const TUTORIAL_POR_ROL = {
        Soporte: [
            {
                seccion: '🎯 Tu flujo principal',
                items: [
                    { ico: '🎫', titulo: 'Crear un ticket',     desc: 'Menú → Nuevo ticket → Rellena el formulario', pregunta: '¿Cómo creo un ticket?' },
                    { ico: '📨', titulo: 'Ver tus tickets',      desc: 'Menú → Ver tickets → Filtra por estado',      pregunta: '¿Cómo veo mis tickets?' },
                    { ico: '⭐', titulo: 'Calificar resolución', desc: 'En ticket resuelto → botón de calificación',  pregunta: '¿Cómo califico un ticket?' }
                ]
            },
            {
                seccion: '❓ Preguntas frecuentes',
                items: [
                    { ico: '🔴', titulo: 'Tipos de ticket',   desc: 'Incidencia, Petición o Consulta', pregunta: '¿Qué tipos de ticket existen?' },
                    { ico: '⚡', titulo: 'Prioridades',       desc: 'Crítica, Alta, Media, Baja',      pregunta: '¿Qué significa la prioridad?' },
                    { ico: '❌', titulo: 'Cancelar ticket',   desc: 'Solo si aún no está cerrado',     pregunta: '¿Cómo cancelo un ticket?' }
                ]
            }
        ],
        Programador: [
            {
                seccion: '🎯 Tu flujo principal',
                items: [
                    { ico: '🔧', titulo: 'Resolver tickets',      desc: 'Menú → Resolver tickets → Tickets asignados a ti', pregunta: '¿Cómo resuelvo un ticket?' },
                    { ico: '📁', titulo: 'Ver proyectos',         desc: 'Menú → Ver proyectos → Tus proyectos activos',     pregunta: '¿Cómo veo mis proyectos?' },
                    { ico: '📋', titulo: 'Nueva actividad',       desc: 'Menú → Nueva actividad → Asigna a un sprint',      pregunta: '¿Cómo creo una actividad?' }
                ]
            },
            {
                seccion: '📚 Conceptos clave',
                items: [
                    { ico: '🏃', titulo: '¿Qué es un sprint?',    desc: 'Período corto de trabajo con actividades', pregunta: '¿Qué es un sprint?' },
                    { ico: '📊', titulo: 'Story points',          desc: 'Medida de esfuerzo de una actividad',      pregunta: '¿Qué son los story points?' },
                    { ico: '📈', titulo: 'Registrar avance',      desc: 'Dentro del proyecto → Nuevo avance',       pregunta: '¿Cómo registro un avance?' }
                ]
            }
        ],
        Admin: [
            {
                seccion: '🎯 Acciones principales',
                items: [
                    { ico: '✅', titulo: 'Aprobar proyectos',       desc: 'Menú → Aprobación de proyectos', pregunta: '¿Cómo apruebo un proyecto?' },
                    { ico: '🚀', titulo: 'Nuevo proyecto',          desc: 'Menú → Nuevo proyecto',          pregunta: '¿Cómo creo un proyecto?' },
                    { ico: '📦', titulo: 'Gestionar aplicaciones',  desc: 'Menú → Aplicaciones',            pregunta: '¿Cómo gestiono aplicaciones?' }
                ]
            },
            {
                seccion: '📊 Métricas y reportes',
                items: [
                    { ico: '📊', titulo: 'Ver indicadores KPI',    desc: 'Menú → Indicadores',          pregunta: '¿Qué indicadores hay?' },
                    { ico: '📈', titulo: 'Generar reportes Excel', desc: 'Menú → Reportes → Exportar',  pregunta: '¿Cómo genero reportes?' },
                    { ico: '👥', titulo: 'Gestionar usuarios',     desc: 'Menú → Lista de Usuarios',    pregunta: '¿Cómo gestiono usuarios?' }
                ]
            }
        ],
        Agente: [
            {
                seccion: '🎯 Tu flujo principal',
                items: [
                    { ico: '📨', titulo: 'Ver tickets asignados', desc: 'Menú → Ver tickets',      pregunta: '¿Cómo veo mis tickets?' },
                    { ico: '🔧', titulo: 'Resolver tickets',      desc: 'Menú → Resolver tickets', pregunta: '¿Cómo resuelvo un ticket?' }
                ]
            }
        ]
    };

    // ═══════════════════════════════════════════════════════
    //  RESPUESTAS DINÁMICAS
    // ═══════════════════════════════════════════════════════
    function respuestaDinamica(tipo) {
        const nombre = usuario.nombre_completo.split(' ')[0];
        const rol    = usuario.rol_nombre;

        if (tipo === 'saludo') {
            const saludos = {
                Admin:       '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿\nComo <strong>administrador</strong> tienes acceso completo. Puedo ayudarte con proyectos, tickets, indicadores, reportes y usuarios.\n\n¿Qué necesitas hoy?',
                Programador: '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿\nComo <strong>programador</strong> puedes resolver tickets, ver tus proyectos y registrar actividades.\n\n¿En qué te ayudo?',
                Soporte:     '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿\nComo <strong>soporte</strong> puedes crear y hacer seguimiento de tus tickets.\n\n¿Qué necesitas hoy?',
                Agente:      '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿\nComo <strong>agente</strong> puedes ver y resolver los tickets asignados a ti.\n\n¿En qué te ayudo?'
            };
            return saludos[rol] || saludos.Soporte;
        }

        if (tipo === 'quePuedo') {
            const acciones = {
                Admin:       'Como <strong>administrador</strong> tienes acceso completo:\n\n🎫 Gestionar todos los tickets\n🚀 Crear y aprobar proyectos\n📊 Ver indicadores KPI\n📈 Generar reportes Excel\n👥 Administrar usuarios\n📦 Gestionar aplicaciones\n\n¿Sobre cuál quieres saber más?',
                Programador: 'Como <strong>programador</strong> puedes:\n\n🎫 Crear tickets de soporte\n🔧 Resolver tickets asignados a ti\n📁 Ver proyectos en los que participas\n📋 Registrar actividades por sprint\n📈 Registrar avances de proyecto\n\n¿Quieres que te explique alguno?',
                Soporte:     'Como <strong>soporte</strong> puedes:\n\n🎫 Crear tickets de incidencia, petición o consulta\n📨 Ver el estado de tus tickets\n⭐ Calificar tickets resueltos\n❌ Cancelar tickets propios\n\n¿Quieres que te explique cómo hacer algo?',
                Agente:      'Como <strong>agente</strong> puedes:\n\n📨 Ver los tickets asignados a ti\n🔧 Resolver los tickets asignados\n\n¿Te explico cómo resolver un ticket?'
            };
            return acciones[rol] || acciones.Soporte;
        }
        return null;
    }

    // ═══════════════════════════════════════════════════════
    //  MOTOR DE BÚSQUEDA EN FAQ
    // ═══════════════════════════════════════════════════════
    function normalizar(texto) {
        return texto.toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[¿¡?!.,;:"'']/g, '')
            .trim();
    }

    function buscarEnFAQ(texto) {
        const t = normalizar(texto);

        if (['hola','buenas','buenos dias','buenas tardes','buenas noches','hey','saludos','hi'].some(function (p) { return t.includes(normalizar(p)); }))
            return { tipo: 'dinamico', subtipo: 'saludo' };

        if (['puedo hacer','que puedo','como empiezo','por donde empiezo','como funciona','ayudame'].some(function (p) { return t.includes(normalizar(p)); }))
            return { tipo: 'dinamico', subtipo: 'quePuedo' };

        for (var i = 0; i < FAQ_GENERAL.length; i++) {
            var faq = FAQ_GENERAL[i];
            if (faq.patrones.some(function (p) { return t.includes(normalizar(p)); }))
                return { tipo: 'fijo', respuesta: faq.respuesta };
        }

        var rolFAQ = FAQ_POR_ROL[usuario.rol_nombre];
        if (rolFAQ) {
            for (var j = 0; j < rolFAQ.length; j++) {
                var faqR = rolFAQ[j];
                if (faqR.patrones.some(function (p) { return t.includes(normalizar(p)); }))
                    return { tipo: 'fijo', respuesta: faqR.respuesta };
            }
        }

        return null;
    }

    // ═══════════════════════════════════════════════════════
    //  LLAMADA A GROQ API — con historial de conversación
    // ═══════════════════════════════════════════════════════
    async function llamarGroq(pregunta) {
        groqKeyIndex = 0;
        var keysValidas = GROQ_KEYS.filter(function (k) { return k && k.trim() !== ''; });
        if (!keysValidas.length)
            return '⚠️ No hay API Keys configuradas. Agrega tus keys en <strong>keys.js</strong>.';

        while (groqKeyIndex < keysValidas.length) {
            var key = keysValidas[groqKeyIndex];
            try {
                var messages = [{ role: 'system', content: systemPrompt }]
                    .concat(convHistory.slice(-MAX_HISTORY))
                    .concat([{ role: 'user', content: pregunta }]);

                var resp = await fetch(GROQ_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type':  'application/json',
                        'Authorization': 'Bearer ' + key
                    },
                    body: JSON.stringify({
                        model:       'llama-3.1-8b-instant',
                        temperature: 0.5,
                        max_tokens:  512,
                        messages:    messages
                    })
                });

                if (resp.status === 429) { groqKeyIndex++; continue; }
                if (!resp.ok) { groqKeyIndex++; continue; }

                var data  = await resp.json();
                var texto = data && data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
                if (!texto) { groqKeyIndex++; continue; }

                convHistory.push({ role: 'user',      content: pregunta });
                convHistory.push({ role: 'assistant',  content: texto });

                return texto
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g,     '<em>$1</em>')
                    .replace(/\n/g,            '<br>');

            } catch (err) {
                groqKeyIndex++;
            }
        }

        return '⚠️ Todas las cuentas alcanzaron su límite por hoy. El FAQ sigue funcionando sin internet.';
    }

    // ═══════════════════════════════════════════════════════
    //  CHIPS Y TUTORIAL
    // ═══════════════════════════════════════════════════════
    function getChips(rol) {
        var chips = {
            Soporte:     ['¿Cómo creo un ticket?', '¿Tipos de ticket?', '¿Estados del ticket?'],
            Programador: ['¿Cómo resuelvo un ticket?', '¿Qué es un sprint?', '¿Cómo creo una actividad?'],
            Admin:       ['¿Cómo apruebo proyectos?', '¿Qué indicadores hay?', '¿Cómo genero reportes?'],
            Agente:      ['¿Cómo veo mis tickets?', '¿Cómo resuelvo un ticket?']
        };
        return chips[rol] || chips.Soporte;
    }

    // ═══════════════════════════════════════════════════════
    //  RENDER DEL WIDGET
    // ═══════════════════════════════════════════════════════
    function render(savedMsgs) {
        var rol      = usuario.rol_nombre;
        var chips    = getChips(rol);
        var tutorial = TUTORIAL_POR_ROL[rol] || [];

        var tutHTML = '';
        tutorial.forEach(function (sec) {
            tutHTML += '<div class="av-tut-seccion"><h4>' + sec.seccion + '</h4>';
            sec.items.forEach(function (it) {
                tutHTML += '<div class="av-tut-item" onclick="AV_CHATBOT.preguntarDesde(\'' + it.pregunta.replace(/'/g, "\\'") + '\')">'
                    + '<div class="av-tut-ico">' + it.ico + '</div>'
                    + '<div class="av-tut-texto"><strong>' + it.titulo + '</strong><span>' + it.desc + '</span></div>'
                    + '</div>';
            });
            tutHTML += '</div>';
        });

        var chipsHTML = chips.map(function (c) {
            return '<button class="av-chip" onclick="AV_CHATBOT.preguntarDesde(\'' + c.replace(/'/g, "\\'") + '\')">' + c + '</button>';
        }).join('');

        var widget = document.createElement('div');
        widget.innerHTML = '<button id="av-chat-btn" onclick="AV_CHATBOT.toggle()" title="AgroBot - Asistente">'
            + '<span id="av-chat-ico">🤖</span>'
            + '<span class="av-badge" id="av-badge">1</span>'
            + '</button>'
            + '<div id="av-chat-window">'
            + '<div id="av-chat-header">'
            + '<div class="av-chat-avatar">🤖</div>'
            + '<div class="av-chat-info"><strong>AgroBot</strong><span>🌿 Asistente de AGROVISION · ' + rol + '</span></div>'
            + '<div class="av-chat-header-btns">'
            + '<button onclick="AV_CHATBOT.limpiar()" title="Limpiar chat">🗑️</button>'
            + '<button onclick="AV_CHATBOT.toggle()" title="Cerrar">✕</button>'
            + '</div></div>'
            + '<div id="av-chat-tabs">'
            + '<button class="av-tab activo" onclick="AV_CHATBOT.setTab(\'chat\', this)">🤖 Chat</button>'
            + '<button class="av-tab" onclick="AV_CHATBOT.setTab(\'tutorial\', this)">🗺️ Tutorial</button>'
            + '</div>'
            + '<div id="av-chat-mensajes"></div>'
            + '<div id="av-panel-tutorial">' + tutHTML + '</div>'
            + '<div class="av-chips" id="av-chips">' + chipsHTML + '</div>'
            + '<div id="av-chat-input-wrap">'
            + '<input type="text" id="av-chat-input" placeholder="Escribe tu pregunta..." onkeydown="if(event.key===\'Enter\') AV_CHATBOT.enviar()">'
            + '<button id="av-chat-send" onclick="AV_CHATBOT.enviar()">➤</button>'
            + '</div></div>';

        document.body.appendChild(widget);

        // Restaurar historial si existe
        if (savedMsgs && savedMsgs.length > 0) {
            savedMsgs.forEach(function (m) {
                addMsg(m.tipo, m.html, false);
            });
        }

        setTimeout(function () {
            if (!savedMsgs || savedMsgs.length === 0) {
                addMsg('bot', respuestaDinamica('saludo'), true);
            }
            var badge = document.getElementById('av-badge');
            if (badge) badge.classList.add('visible');
        }, 800);
    }

    // ═══════════════════════════════════════════════════════
    //  MENSAJES
    // ═══════════════════════════════════════════════════════
    function addMsg(tipo, html, persistir) {
        var cont = document.getElementById('av-chat-mensajes');
        if (!cont) return;
        var div = document.createElement('div');
        div.className = 'av-msg ' + tipo;
        div.innerHTML = tipo === 'bot'
            ? '<div class="av-msg-ico">🤖</div><div class="av-msg-burbuja">' + html + '</div>'
            : '<div class="av-msg-burbuja">' + html + '</div>';
        cont.appendChild(div);
        cont.scrollTop = cont.scrollHeight;

        if (persistir !== false) persistirMensajes();
    }

    var _mensajesDisplay = [];

    function persistirMensajes() {
        var cont = document.getElementById('av-chat-mensajes');
        if (!cont) return;
        var msgs = [];
        cont.querySelectorAll('.av-msg').forEach(function (el) {
            var burbuja = el.querySelector('.av-msg-burbuja');
            if (burbuja) {
                msgs.push({
                    tipo: el.classList.contains('bot') ? 'bot' : 'user',
                    html: burbuja.innerHTML
                });
            }
        });
        _mensajesDisplay = msgs;
        saveHistory(msgs);
    }

    function addTyping() {
        var cont = document.getElementById('av-chat-mensajes');
        if (!cont) return;
        var div = document.createElement('div');
        div.className = 'av-msg bot';
        div.id = 'av-typing';
        div.innerHTML = '<div class="av-msg-ico">🤖</div><div class="av-typing"><span></span><span></span><span></span></div>';
        cont.appendChild(div);
        cont.scrollTop = cont.scrollHeight;
    }

    function removeTyping() {
        var t = document.getElementById('av-typing');
        if (t) t.remove();
    }

    // ═══════════════════════════════════════════════════════
    //  API PÚBLICA
    // ═══════════════════════════════════════════════════════
    function toggle() {
        var win   = document.getElementById('av-chat-window');
        var ico   = document.getElementById('av-chat-ico');
        var badge = document.getElementById('av-badge');
        if (!win) return;
        abierto = !abierto;
        win.classList.toggle('abierto', abierto);
        if (ico)   ico.textContent = abierto ? '✕' : '🤖';
        if (badge) badge.classList.remove('visible');
    }

    function setTab(tab, btn) {
        var mensajes = document.getElementById('av-chat-mensajes');
        var tutorial = document.getElementById('av-panel-tutorial');
        var chips    = document.getElementById('av-chips');
        var inputW   = document.getElementById('av-chat-input-wrap');
        document.querySelectorAll('.av-tab').forEach(function (t) { t.classList.remove('activo'); });
        btn.classList.add('activo');
        if (tab === 'chat') {
            if (mensajes) mensajes.style.display = 'flex';
            if (tutorial) tutorial.classList.remove('activo');
            if (chips)    chips.style.display    = 'flex';
            if (inputW)   inputW.style.display   = 'flex';
        } else {
            if (mensajes) mensajes.style.display = 'none';
            if (tutorial) tutorial.classList.add('activo');
            if (chips)    chips.style.display    = 'none';
            if (inputW)   inputW.style.display   = 'none';
        }
    }

    function limpiar() {
        var cont = document.getElementById('av-chat-mensajes');
        if (cont) cont.innerHTML = '';
        var ico = document.getElementById('av-chat-ico');
        if (ico) ico.textContent = '🤖';
        convHistory = [];
        _mensajesDisplay = [];
        saveHistory([]);
        setTimeout(function () { addMsg('bot', respuestaDinamica('saludo'), true); }, 100);
    }

    async function enviar() {
        var input = document.getElementById('av-chat-input');
        var btn   = document.getElementById('av-chat-send');
        if (!input) return;
        var texto = input.value.trim();
        if (!texto) return;

        input.value = '';
        if (btn) btn.disabled = true;
        addMsg('user', texto, true);

        var tabs = document.querySelectorAll('.av-tab');
        if (tabs[0] && !tabs[0].classList.contains('activo')) setTab('chat', tabs[0]);

        var faqResult = buscarEnFAQ(texto);

        if (faqResult) {
            addTyping();
            await new Promise(function (r) { setTimeout(r, 400); });
            removeTyping();
            var resp = faqResult.tipo === 'dinamico'
                ? respuestaDinamica(faqResult.subtipo)
                : faqResult.respuesta;
            addMsg('bot', resp, true);

            if (faqResult.tipo === 'dinamico' && faqResult.subtipo === 'saludo') {
                convHistory.push({ role: 'user', content: texto });
                convHistory.push({ role: 'assistant', content: resp.replace(/<br>/g, '\n').replace(/<strong>/g, '').replace(/<\/strong>/g, '') });
                saveHistory(_mensajesDisplay);
            }
        } else {
            addTyping();
            try {
                var respuesta = await llamarGroq(texto);
                removeTyping();
                addMsg('bot', respuesta, true);
            } catch (err) {
                removeTyping();
                addMsg('bot', '⚠️ No pude conectarme a la IA. Revisa tu conexión e intenta de nuevo.', true);
                console.error('Groq error:', err);
            }
        }

        if (btn) btn.disabled = false;
        input.focus();
    }

    function preguntarDesde(texto) {
        var tabs = document.querySelectorAll('.av-tab');
        if (tabs[0]) setTab('chat', tabs[0]);
        var input = document.getElementById('av-chat-input');
        if (input) { input.value = texto; enviar(); }
    }

    // ═══════════════════════════════════════════════════════
    //  INICIALIZACIÓN
    // ═══════════════════════════════════════════════════════
    async function init() {
        usuario = await initUsuario();
        if (!usuario) return; // no renderizar si no hay usuario

        systemPrompt = buildSystemPrompt(usuario);

        var savedMsgs = loadHistory();

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function () { render(savedMsgs); });
        } else {
            render(savedMsgs);
        }
    }

    init();

    return { toggle: toggle, setTab: setTab, limpiar: limpiar, enviar: enviar, preguntarDesde: preguntarDesde };

})();
