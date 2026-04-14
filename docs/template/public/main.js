import WorkflowContainer from "./workflow.js"

export default {
    defaultTheme: 'light',
    iconLinks: [{
        icon: 'github',
        href: 'https://github.com/ucl-open/ucl-open',
        title: 'GitHub'
    }],
    start: () => {
        WorkflowContainer.init();
    }
}
