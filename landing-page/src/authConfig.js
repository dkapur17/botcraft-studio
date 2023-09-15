import { LogLevel } from '@azure/msal-browser';

export const msalConfig = {
    auth: {
      clientId: '0c84f826-856e-4cd0-92a7-b6c0750204b3',
      authority: 'https://login.microsoftonline.com/organizations',
        redirectUri: '/',
        postLogoutRedirectUri: '/',
        navigateToLoginRequestUrl: false,
    },
    system: {
        loggerOptions: {
            loggerCallback: (level, message, containsPii) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case LogLevel.Error:
                        console.error(message);
                        return;
                    case LogLevel.Info:
                        console.info(message);
                        return;
                    case LogLevel.Verbose:
                        console.debug(message);
                        return;
                    case LogLevel.Warning:
                        console.warn(message);
                        return;
                    default:
                        return;
                }
            },
        },
    },
};


export const loginRequest = {
    scopes: [],
};