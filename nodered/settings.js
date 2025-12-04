/**
 * Node-RED Settings for OptiFlow
 * ===============================
 * READ-ONLY industrial protocol validation
 */
module.exports = {
    // Flow file
    flowFile: 'flows.json',

    // User directory
    userDir: '/data',

    // Editor theme
    editorTheme: {
        projects: {
            enabled: false
        },
        header: {
            title: "OptiFlow Node-RED - Protocol Validation",
            image: null,
            url: null
        },
        page: {
            title: "OptiFlow Node-RED"
        }
    },

    // Logging
    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },

    // Function node settings
    functionGlobalContext: {
        // Add global context objects here
    },

    // Context storage
    contextStorage: {
        default: {
            module: "memory"
        }
    },

    // Export global context
    exportGlobalContextKeys: false,

    // Disable unnecessary features for security
    disableEditor: false,
    httpAdminRoot: '/',
    httpNodeRoot: '/api',

    // API settings
    apiMaxLength: '5mb'
};
