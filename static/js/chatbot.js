const AV_CHATBOT = (function () {

    const GROQ_KEYS = typeof GROQ_KEYS_LOCAL !== 'undefined' ? GROQ_KEYS_LOCAL : [];
    const GROQ_URL  = 'https://api.groq.com/openai/v1/chat/completions';
    const STORAGE_PREFIX = 'av-chat-';
    const MAX_HISTORY    = 10;
    const MAX_SAVED_MSGS = 50;

    let groqKeyIndex = 0;
    let usuario      = null;
    let systemPrompt = '';
    let convHistory  = [];
    let abierto      = false;

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

    function buildSystemPrompt(u) {
        const rol    = u.rol_nombre;
        const nombre = u.nombre_completo;

        const base = 'Eres AgroBot, el asistente virtual de AGROVISION, un sistema de gestión empresarial peruano.\n'
                   + 'Responde siempre en español, de forma amigable, clara y concisa. Máximo 4 líneas por respuesta.\n'
                   + 'Usa emojis con moderación. Usa etiquetas HTML <strong> para resaltar términos importantes.\n'
                   + 'El usuario se llama ' + nombre + ' y tiene rol: ' + rol + '.\n'
                   + 'IMPORTANTE: Solo responde preguntas relacionadas con AGROVISION.\n'
                   + 'Si el usuario pregunta algo que su rol NO puede hacer, explícale claramente.\n'
                   + 'No menciones que eres una IA de Groq o Meta. Eres AgroBot de AGROVISION.';

        const contextos = {
            Admin:       '\nROL ADMIN — acceso total: Dashboard, todos los tickets, aplicaciones, proyectos, aprobación, actividades, indicadores KPI, usuarios, reportes Excel.',
            Programador: '\nROL PROGRAMADOR — acceso parcial: Dashboard, crear ticket, ver sus tickets, resolver tickets asignados, proyectos donde participa, nueva actividad. NO puede: Crear/aprobar proyectos, aplicaciones, indicadores, reportes, usuarios.',
            Soporte:     '\nROL SOPORTE — acceso básico: Dashboard, crear tickets, ver sus tickets, calificar tickets resueltos, cancelar sus tickets. NO puede: Resolver tickets, proyectos, actividades, aplicaciones, indicadores, reportes, usuarios.',
            Agente:      '\nROL AGENTE — solo tickets asignados. NO puede: Proyectos, actividades, aplicaciones, indicadores, reportes, usuarios.'
        };

        var contextoReal = '';
        if (u._contexto && u._contexto.resumen) {
            var r = u._contexto.resumen;
            contextoReal = '\n\nDATOS REALES DEL USUARIO (consulta en vivo de la BD):';

            if (rol === 'Soporte') {
                contextoReal += '\n- Tickets abiertos que creó: ' + r.tickets_abiertos
                             + '\n- Tickets resueltos: ' + r.tickets_resueltos;
            } else if (rol === 'Programador') {
                contextoReal += '\n- Tickets asignados para resolver: ' + r.tickets_asignados
                             + '\n- Tickets resueltos: ' + r.tickets_resueltos
                             + '\n- Proyectos activos: ' + r.proyectos_activos
                             + '\n- Actividades pendientes: ' + r.actividades_pendientes;
            } else {
                contextoReal += '\n- Tickets abiertos: ' + r.tickets_abiertos
                             + '\n- Tickets resueltos: ' + r.tickets_resueltos
                             + '\n- Tickets asignados para resolver: ' + r.tickets_asignados
                             + '\n- Proyectos activos: ' + r.proyectos_activos
                             + '\n- Actividades pendientes: ' + r.actividades_pendientes;
            }

            if (u._contexto.tickets_abiertos && u._contexto.tickets_abiertos.length > 0) {
                contextoReal += '\nDetalle tickets abiertos: '
                    + u._contexto.tickets_abiertos.map(function(t) {
                        return 'SD-' + t.id + ' [' + t.prioridad + '] ' + t.titulo;
                    }).join(' | ');
            }
            if (u._contexto.tickets_asignados && u._contexto.tickets_asignados.length > 0) {
                contextoReal += '\nDetalle tickets asignados: '
                    + u._contexto.tickets_asignados.map(function(t) {
                        return 'SD-' + t.id + ' [' + t.prioridad + '] ' + t.titulo;
                    }).join(' | ');
            }
            if (u._contexto.proyectos && u._contexto.proyectos.length > 0) {
                contextoReal += '\nProyectos: '
                    + u._contexto.proyectos.map(function(p) {
                        return p.nombre + ' [' + p.estado + '] ' + p.completadas + '/' + p.total_acts + ' acts';
                    }).join(' | ');
            }
            if (u._contexto.actividades_pendientes && u._contexto.actividades_pendientes.length > 0) {
                contextoReal += '\nActividades pendientes: '
                    + u._contexto.actividades_pendientes.map(function(a) {
                        return a.titulo + ' [' + a.estado + ', ' + a.prioridad + ']';
                    }).join(' | ');
            }
            contextoReal += '\nIMPORTANTE: Usa estos datos reales. No inventes números.';
        }

        return base + (contextos[rol] || contextos.Soporte) + contextoReal;
    }

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

    const FAQ_GENERAL = [
        {
            patrones: ['que es agrovision', 'para que sirve', 'de que trata', 'que hace agrovision'],
            respuesta: '🌿 <strong>AGROVISION</strong> es un sistema de gestión empresarial que centraliza:<br><br>• 🎫 <strong>Soporte</strong>: Tickets de incidencias y peticiones<br>• 🚀 <strong>Proyectos</strong>: Gestión ágil con sprints y actividades<br>• 📊 <strong>Indicadores y reportes</strong> en tiempo real'
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
                patrones: ['nuevo ticket', 'crear ticket', 'abrir ticket', 'registrar ticket', 'como creo un ticket', 'como abro un ticket', 'quiero crear un ticket'],
                respuesta: '🎫 Para crear un ticket:<br><br>1. Clic en <strong>"Nuevo ticket"</strong> en el menú lateral<br>2. Escribe un <strong>título claro</strong> del problema<br>3. Selecciona el <strong>tipo</strong>: Incidencia 🔴, Petición 🔵 o Consulta 🟡<br>4. Elige la <strong>aplicación afectada</strong><br>5. Describe el problema con detalle<br>6. Clic en <strong>"Enviar ticket"</strong> 📨'
            },
            {
                patrones: ['ver tickets', 'mis tickets', 'estado ticket', 'estados del ticket', 'listar tickets', 'donde veo mis tickets'],
                respuesta: '📨 Ve a <strong>"Ver tickets"</strong> en el menú lateral.<br><br>Estados posibles:<br>• <strong>Solicitado</strong> → Esperando asignación<br>• <strong>En progreso</strong> → Siendo atendido<br>• <strong>Resuelto</strong> → El agente lo solucionó<br>• <strong>Cerrado</strong> → Confirmado y cerrado<br>• <strong>Cancelado</strong> → Anulado'
            },
            {
                patrones: ['tipo ticket', 'tipos de ticket', 'que tipos', 'incidencia', 'peticion', 'consulta', 'diferencia entre'],
                respuesta: '📋 Los tipos de ticket son:<br><br>🔴 <strong>Incidencia</strong>: Algo que no funciona, un error o falla<br>🔵 <strong>Petición</strong>: Solicitud de acceso o cuenta nueva<br>🟡 <strong>Consulta</strong>: Pregunta o duda sobre el sistema'
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
                respuesta: '⚡ La prioridad la asigna el agente:<br><br>🚨 <strong>Crítica</strong>: Sistema caído<br>🔴 <strong>Alta</strong>: Afecta a varios usuarios<br>🟡 <strong>Media</strong>: Impacto moderado<br>⚪ <strong>Baja</strong>: Puede esperar'
            },
            {
                patrones: ['resolver ticket', 'resuelvo', 'solucionar ticket', 'atender ticket', 'como resuelvo'],
                respuesta: '🚫 Como <strong>soporte</strong> no puedes resolver tickets, eso lo hace el agente asignado.<br><br>Tu rol es <strong>crear tickets</strong> y hacer seguimiento. Cuando el agente lo resuelva podrás <strong>calificarlo</strong> ⭐'
            },
            {
                patrones: ['ver proyectos', 'crear proyecto', 'nuevo proyecto', 'acceder proyectos', 'donde estan proyectos'],
                respuesta: '🚫 Como <strong>soporte</strong> no tienes acceso a proyectos. Esa sección es para programadores y administradores.<br><br>Tu área es el <strong>módulo de tickets</strong> 🎫'
            },
            {
                patrones: ['indicadores', 'reportes', 'kpi', 'metricas', 'estadisticas', 'ver indicadores'],
                respuesta: '🚫 Como <strong>soporte</strong> no tienes acceso a indicadores ni reportes. Esa sección es exclusiva del administrador.'
            },
            { patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'], respuesta: null }
        ],
        Programador: [
            {
                patrones: ['resolver ticket', 'resuelvo', 'como resuelvo', 'atender ticket', 'solucionar ticket', 'resolver un ticket', 'como resuelvo un ticket'],
                respuesta: '🔧 Para resolver un ticket:<br><br>1. Ve a <strong>"Resolver tickets"</strong> en el menú lateral<br>2. Verás los tickets asignados a ti<br>3. Haz clic en <strong>"Resolver"</strong><br>4. Completa la descripción de la solución<br>5. Guarda para marcarlo como resuelto'
            },
            {
                patrones: ['ver proyectos', 'mis proyectos', 'listar proyectos', 'donde veo proyectos', 'como veo proyectos'],
                respuesta: '📁 Ve a <strong>"Ver proyectos"</strong> en el menú. Verás los proyectos en los que participas.'
            },
            {
                patrones: ['sprint', 'sprints', 'que es un sprint', 'que son los sprints', 'para que sirve un sprint'],
                respuesta: '🏃 Un <strong>sprint</strong> es un período de trabajo corto (1-2 semanas) donde el equipo completa un conjunto de actividades con story points.'
            },
            {
                patrones: ['nueva actividad', 'crear actividad', 'registrar actividad', 'como creo una actividad', 'quiero crear una actividad', 'agregar actividad'],
                respuesta: '📋 Para crear una actividad:<br><br>1. Clic en <strong>"Nueva actividad"</strong> en el menú<br>2. El código se genera automáticamente<br>3. Escribe el título<br>4. Selecciona el <strong>proyecto</strong> y el <strong>sprint</strong><br>5. Asigna responsable, prioridad y story points<br>6. Guarda'
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
                patrones: ['nuevo proyecto', 'crear proyecto', 'registrar proyecto', 'como creo un proyecto', 'quiero crear proyecto'],
                respuesta: '🚫 Como <strong>programador</strong> no puedes crear proyectos. Solo el <strong>administrador</strong> puede crearlos y aprobarlos.'
            },
            {
                patrones: ['indicadores', 'reportes', 'kpi', 'metricas', 'estadisticas'],
                respuesta: '🚫 Como <strong>programador</strong> no tienes acceso a indicadores ni reportes. Esa sección es exclusiva del <strong>administrador</strong>.'
            },
            { patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'], respuesta: null }
        ],
        Admin: [
            {
                patrones: ['aprobar proyecto', 'aprobacion proyecto', 'rechazar proyecto', 'como apruebo', 'revisar proyectos'],
                respuesta: '✅ Para aprobar o rechazar proyectos:<br><br>1. Ve a <strong>"Aprobación de proyectos"</strong> en el menú<br>2. Verás los proyectos con estado <strong>"En revisión"</strong><br>3. Elige <strong>Aprobar</strong> ✅ o <strong>Rechazar</strong> ❌<br>4. Al aprobar se generan automáticamente los sprints'
            },
            {
                patrones: ['nuevo proyecto', 'crear proyecto', 'registrar proyecto', 'como creo un proyecto', 'quiero crear proyecto', 'abrir proyecto'],
                respuesta: '🚀 Para crear un proyecto:<br><br>1. Clic en <strong>"Nuevo proyecto"</strong> en el menú<br>2. Escribe el nombre del proyecto<br>3. Selecciona los <strong>Stakeholders</strong><br>4. Fecha de fin planificada<br>5. Describe la problemática y solución'
            },
            {
                patrones: ['gestionar usuarios', 'lista usuarios', 'ver usuarios', 'buscar usuario', 'administrar usuarios'],
                respuesta: '👥 Ve a <strong>"Lista de Usuarios"</strong> en el menú. Puedes buscar por nombre y ver el perfil completo con estadísticas e historial.'
            },
            {
                patrones: ['indicadores', 'kpi', 'metricas', 'estadisticas', 'ver indicadores', 'que indicadores'],
                respuesta: '📊 Los <strong>indicadores</strong> están en el menú lateral. Incluyen KPIs de tickets, satisfacción, velocidad por sprint, carga de programadores, estado de proyectos y SLA por agente.'
            },
            {
                patrones: ['reportes', 'reporte', 'informe', 'exportar', 'excel', 'generar reporte'],
                respuesta: '📈 Ve a <strong>"Reportes"</strong> en el menú. Puedes generar y exportar a <strong>Excel</strong>: tickets, story points, sprints, proyectos en riesgo, SLA y tendencia por mes.'
            },
            {
                patrones: ['aplicaciones', 'gestionar aplicaciones', 'nueva aplicacion', 'ver aplicaciones'],
                respuesta: '📦 En <strong>"Aplicaciones"</strong> puedes ver, crear, editar y activar/desactivar aplicaciones. Las aplicaciones se asocian a los tickets de soporte.'
            },
            { patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'], respuesta: null }
        ],
        Agente: [
            {
                patrones: ['mis tickets', 'tickets asignados', 'ver mis tickets', 'donde veo mis tickets'],
                respuesta: '📨 Ve a <strong>"Ver tickets"</strong> en el menú. Solo verás los tickets asignados a ti.'
            },
            {
                patrones: ['resolver ticket', 'resuelvo', 'como resuelvo', 'solucionar', 'atender'],
                respuesta: '🔧 Para resolver un ticket:<br><br>1. Ve a <strong>"Resolver tickets"</strong> en el menú<br>2. Haz clic en <strong>"Resolver"</strong><br>3. Llena la descripción de la solución<br>4. Guarda → queda como <strong>Resuelto</strong>'
            },
            {
                patrones: ['ver proyectos', 'crear proyecto', 'indicadores', 'reportes', 'lista usuarios'],
                respuesta: '🚫 Como <strong>agente</strong> tu acceso está limitado a los tickets asignados a ti.'
            },
            { patrones: ['puedo hacer', 'que puedo', 'empezar', 'empiezo', 'como funciona', 'ayuda'], respuesta: null }
        ]
    };

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
                    { ico: '🔴', titulo: 'Tipos de ticket', desc: 'Incidencia, Petición o Consulta', pregunta: '¿Qué tipos de ticket existen?' },
                    { ico: '⚡', titulo: 'Prioridades',     desc: 'Crítica, Alta, Media, Baja',      pregunta: '¿Qué significa la prioridad?' },
                    { ico: '❌', titulo: 'Cancelar ticket', desc: 'Solo si aún no está cerrado',     pregunta: '¿Cómo cancelo un ticket?' }
                ]
            }
        ],
        Programador: [
            {
                seccion: '🎯 Tu flujo principal',
                items: [
                    { ico: '🔧', titulo: 'Resolver tickets', desc: 'Menú → Resolver tickets → Tickets asignados a ti', pregunta: '¿Cómo resuelvo un ticket?' },
                    { ico: '📁', titulo: 'Ver proyectos',    desc: 'Menú → Ver proyectos → Tus proyectos activos',     pregunta: '¿Cómo veo mis proyectos?' },
                    { ico: '📋', titulo: 'Nueva actividad',  desc: 'Menú → Nueva actividad → Asigna a un sprint',      pregunta: '¿Cómo creo una actividad?' }
                ]
            },
            {
                seccion: '📚 Conceptos clave',
                items: [
                    { ico: '🏃', titulo: '¿Qué es un sprint?', desc: 'Período corto de trabajo con actividades', pregunta: '¿Qué es un sprint?' },
                    { ico: '📊', titulo: 'Story points',       desc: 'Medida de esfuerzo de una actividad',      pregunta: '¿Qué son los story points?' },
                    { ico: '📈', titulo: 'Registrar avance',   desc: 'Dentro del proyecto → Nuevo avance',       pregunta: '¿Cómo registro un avance?' }
                ]
            }
        ],
        Admin: [
            {
                seccion: '🎯 Acciones principales',
                items: [
                    { ico: '✅', titulo: 'Aprobar proyectos',      desc: 'Menú → Aprobación de proyectos', pregunta: '¿Cómo apruebo un proyecto?' },
                    { ico: '🚀', titulo: 'Nuevo proyecto',         desc: 'Menú → Nuevo proyecto',          pregunta: '¿Cómo creo un proyecto?' },
                    { ico: '📦', titulo: 'Gestionar aplicaciones', desc: 'Menú → Aplicaciones',            pregunta: '¿Cómo gestiono aplicaciones?' }
                ]
            },
            {
                seccion: '📊 Métricas y reportes',
                items: [
                    { ico: '📊', titulo: 'Ver indicadores KPI',    desc: 'Menú → Indicadores',         pregunta: '¿Qué indicadores hay?' },
                    { ico: '📈', titulo: 'Generar reportes Excel', desc: 'Menú → Reportes → Exportar', pregunta: '¿Cómo genero reportes?' },
                    { ico: '👥', titulo: 'Gestionar usuarios',     desc: 'Menú → Lista de Usuarios',   pregunta: '¿Cómo gestiono usuarios?' }
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

    function respuestaDinamica(tipo) {
        const nombre = usuario.nombre_completo.split(' ')[0];
        const rol    = usuario.rol_nombre;

        if (tipo === 'saludo') {
            const saludos = {
                Admin:       '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿<br>Como <strong>administrador</strong> tienes acceso completo. Puedo ayudarte con proyectos, tickets, indicadores, reportes y usuarios.<br><br>¿Qué necesitas hoy?',
                Programador: '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿<br>Como <strong>programador</strong> puedes resolver tickets, ver tus proyectos y registrar actividades.<br><br>¿En qué te ayudo?',
                Soporte:     '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿<br>Como <strong>soporte</strong> puedes crear y hacer seguimiento de tus tickets.<br><br>¿Qué necesitas hoy?',
                Agente:      '👋 ¡Hola <strong>' + nombre + '</strong>! Soy AgroBot 🌿<br>Como <strong>agente</strong> puedes ver y resolver los tickets asignados a ti.<br><br>¿En qué te ayudo?'
            };
            return saludos[rol] || saludos.Soporte;
        }

        if (tipo === 'quePuedo') {
            const acciones = {
                Admin:       'Como <strong>administrador</strong> tienes acceso completo:<br><br>🎫 Gestionar todos los tickets<br>🚀 Crear y aprobar proyectos<br>📊 Ver indicadores KPI<br>📈 Generar reportes Excel<br>👥 Administrar usuarios<br>📦 Gestionar aplicaciones',
                Programador: 'Como <strong>programador</strong> puedes:<br><br>🎫 Crear tickets de soporte<br>🔧 Resolver tickets asignados<br>📁 Ver proyectos en los que participas<br>📋 Registrar actividades por sprint<br>📈 Registrar avances de proyecto',
                Soporte:     'Como <strong>soporte</strong> puedes:<br><br>🎫 Crear tickets de incidencia, petición o consulta<br>📨 Ver el estado de tus tickets<br>⭐ Calificar tickets resueltos<br>❌ Cancelar tickets propios',
                Agente:      'Como <strong>agente</strong> puedes:<br><br>📨 Ver los tickets asignados a ti<br>🔧 Resolver los tickets asignados'
            };
            return acciones[rol] || acciones.Soporte;
        }
        return null;
    }

    // ─── normalizar ────────────────────────────────────────
    function normalizar(texto) {
        return texto.toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[¿¡?!.,;:"'']/g, '')
            .trim();
    }

    // ─── buscarEnBD ────────────────────────────────────────
    function buscarEnBD(texto) {
        if (!usuario || !usuario._contexto) return null;
        var t   = normalizar(texto);
        var r   = usuario._contexto.resumen;
        var ctx = usuario._contexto;
        var rol = usuario.rol_nombre;

        // Tickets abiertos (Soporte los ve como los que creó)
        if (['cuantos tickets tengo', 'cuantos tickets', 'tickets abiertos', 'tickets pendientes',
             'tengo tickets abiertos', 'tickets en progreso', 'cuantos tengo abiertos'].some(function(p) { return t.includes(p); })) {
            if (rol === 'Soporte') {
                if (r.tickets_abiertos === 0) return '✅ No tienes tickets abiertos en este momento. Todo al día.';
                var lista = ctx.tickets_abiertos.map(function(tk) {
                    return '<br>• <strong>SD-' + tk.id + '</strong> [' + tk.prioridad + '] ' + tk.titulo;
                }).join('');
                return '🎫 Tienes <strong>' + r.tickets_abiertos + ' ticket(s) abierto(s)</strong>:' + lista;
            }
            return null;
        }

        // Tickets asignados para resolver (Programador / Agente)
        if (['tickets asignados', 'resolver tickets', 'tengo que resolver', 'asignados a mi',
             'tickets para resolver'].some(function(p) { return t.includes(p); })) {
            if (rol === 'Soporte') return '🚫 Como <strong>soporte</strong> no recibes tickets asignados para resolver.';
            if (r.tickets_asignados === 0) return '✅ No tienes tickets asignados para resolver en este momento.';
            var lista2 = ctx.tickets_asignados.map(function(tk) {
                return '<br>• <strong>SD-' + tk.id + '</strong> [' + tk.prioridad + '] ' + tk.titulo;
            }).join('');
            return '🔧 Tienes <strong>' + r.tickets_asignados + ' ticket(s) asignado(s)</strong> para resolver:' + lista2;
        }

        // Proyectos (solo Programador / Admin)
        if (['cuantos proyectos tengo', 'cuantos proyectos', 'proyectos activos tengo',
             'en que proyectos estoy', 'proyectos tengo'].some(function(p) { return t.includes(p); })) {
            if (rol === 'Soporte') return '🚫 Como <strong>soporte</strong> no tienes acceso a proyectos.';
            if (r.proyectos_activos === 0) return '📁 No estás asignado a ningún proyecto activo actualmente.';
            var lista3 = ctx.proyectos.map(function(p) {
                return '<br>• <strong>' + p.nombre + '</strong> [' + p.estado + '] — '
                    + p.completadas + '/' + p.total_acts + ' actividades';
            }).join('');
            return '🚀 Participas en <strong>' + r.proyectos_activos + ' proyecto(s) activo(s)</strong>:' + lista3;
        }

        // Actividades pendientes (solo Programador / Admin)
        if (['mis actividades', 'actividades pendientes', 'cuantas actividades', 'actividades asignadas',
             'que actividades tengo', 'tareas pendientes'].some(function(p) { return t.includes(p); })) {
            if (rol === 'Soporte') return '🚫 Como <strong>soporte</strong> no tienes actividades asignadas.';
            if (r.actividades_pendientes === 0) return '✅ No tienes actividades pendientes asignadas.';
            var lista4 = ctx.actividades_pendientes.map(function(a) {
                return '<br>• <strong>' + a.titulo + '</strong> [' + a.estado + ', ' + a.prioridad + ']';
            }).join('');
            return '📋 Tienes <strong>' + r.actividades_pendientes + ' actividad(es) pendiente(s)</strong>:' + lista4;
        }

        // Resumen general — filtrado por rol
        if (['resumen', 'como estoy', 'estado general', 'mi situacion', 'que tengo pendiente',
             'que tengo', 'mi estado'].some(function(p) { return t.includes(p); })) {
            var resumenHTML = '📊 Tu resumen actual:';

            if (rol === 'Soporte') {
                resumenHTML += '<br>🎫 Tickets abiertos que creaste: <strong>' + r.tickets_abiertos + '</strong>'
                            + '<br>✅ Tickets resueltos: <strong>' + r.tickets_resueltos + '</strong>';
            } else if (rol === 'Programador') {
                resumenHTML += '<br>🔧 Tickets asignados para resolver: <strong>' + r.tickets_asignados + '</strong>'
                            + '<br>✅ Tickets resueltos: <strong>' + r.tickets_resueltos + '</strong>'
                            + '<br>🚀 Proyectos activos: <strong>' + r.proyectos_activos + '</strong>'
                            + '<br>📋 Actividades pendientes: <strong>' + r.actividades_pendientes + '</strong>';
            } else {
                resumenHTML += '<br>🎫 Tickets abiertos: <strong>' + r.tickets_abiertos + '</strong>'
                            + '<br>🔧 Tickets asignados para resolver: <strong>' + r.tickets_asignados + '</strong>'
                            + '<br>✅ Tickets resueltos: <strong>' + r.tickets_resueltos + '</strong>'
                            + '<br>🚀 Proyectos activos: <strong>' + r.proyectos_activos + '</strong>'
                            + '<br>📋 Actividades pendientes: <strong>' + r.actividades_pendientes + '</strong>';
            }
            return resumenHTML;
        }

        return null; // No es pregunta de datos → pasa al FAQ o IA
    }

    // ─── buscarEnFAQ ───────────────────────────────────────
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

    // ─── llamarGroq ────────────────────────────────────────
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
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key },
                    body: JSON.stringify({ model: 'llama-3.1-8b-instant', temperature: 0.5, max_tokens: 512, messages: messages })
                });

                if (resp.status === 429) { groqKeyIndex++; continue; }
                if (!resp.ok)            { groqKeyIndex++; continue; }

                var data  = await resp.json();
                var texto = data && data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
                if (!texto) { groqKeyIndex++; continue; }

                convHistory.push({ role: 'user',      content: pregunta });
                convHistory.push({ role: 'assistant',  content: texto });

                return texto
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g,     '<em>$1</em>')
                    .replace(/\n/g,            '<br>');
            } catch (err) { groqKeyIndex++; }
        }
        return '⚠️ Todas las cuentas alcanzaron su límite por hoy. El FAQ sigue funcionando sin internet.';
    }

    // ─── chips ─────────────────────────────────────────────
    function getChips(rol) {
        var chips = {
            Soporte:     ['¿Cómo creo un ticket?', '¿Tipos de ticket?', '¿Estados del ticket?'],
            Programador: ['¿Cómo resuelvo un ticket?', '¿Qué es un sprint?', '¿Cómo creo una actividad?'],
            Admin:       ['¿Cómo apruebo proyectos?', '¿Qué indicadores hay?', '¿Cómo genero reportes?'],
            Agente:      ['¿Cómo veo mis tickets?', '¿Cómo resuelvo un ticket?']
        };
        return chips[rol] || chips.Soporte;
    }

    // ─── render ────────────────────────────────────────────
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
            + '<span id="av-chat-ico">🤖</span><span class="av-badge" id="av-badge">1</span></button>'
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

        if (savedMsgs && savedMsgs.length > 0) {
            savedMsgs.forEach(function (m) { addMsg(m.tipo, m.html, false); });
        }

        setTimeout(function () {
            if (!savedMsgs || savedMsgs.length === 0) {
                addMsg('bot', respuestaDinamica('saludo'), true);
            }
            var badge = document.getElementById('av-badge');
            if (badge) badge.classList.add('visible');
        }, 800);
    }

    // ─── mensajes ──────────────────────────────────────────
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
            if (burbuja) msgs.push({ tipo: el.classList.contains('bot') ? 'bot' : 'user', html: burbuja.innerHTML });
        });
        _mensajesDisplay = msgs;
        saveHistory(msgs);
    }

    function addTyping() {
        var cont = document.getElementById('av-chat-mensajes');
        if (!cont) return;
        var div = document.createElement('div');
        div.className = 'av-msg bot'; div.id = 'av-typing';
        div.innerHTML = '<div class="av-msg-ico">🤖</div><div class="av-typing"><span></span><span></span><span></span></div>';
        cont.appendChild(div); cont.scrollTop = cont.scrollHeight;
    }

    function removeTyping() { var t = document.getElementById('av-typing'); if (t) t.remove(); }

    // ─── API pública ───────────────────────────────────────
    function toggle() {
        var win = document.getElementById('av-chat-window');
        var ico = document.getElementById('av-chat-ico');
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
        convHistory = []; _mensajesDisplay = []; saveHistory([]);
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

        var bdResult  = buscarEnBD(texto);
        var faqResult = buscarEnFAQ(texto);

        if (bdResult) {
            addTyping();
            await new Promise(function (r) { setTimeout(r, 350); });
            removeTyping();
            addMsg('bot', bdResult, true);

        } else if (faqResult) {
            addTyping();
            await new Promise(function (r) { setTimeout(r, 400); });
            removeTyping();
            var resp = faqResult.tipo === 'dinamico' ? respuestaDinamica(faqResult.subtipo) : faqResult.respuesta;
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

    // ─── init ──────────────────────────────────────────────
    async function init() {
        usuario = await initUsuario();
        if (!usuario) return;

        try {
            var ctxResp = await fetch('/api/chatbot/contexto');
            if (ctxResp.ok) {
                var ctxData = await ctxResp.json();
                if (ctxData.ok) usuario._contexto = ctxData;
            }
        } catch (e) {}

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