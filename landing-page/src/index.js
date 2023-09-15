import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { PublicClientApplication, EventType } from '@azure/msal-browser';
import { msalConfig } from './authConfig';

import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/index.css';


const msalInstance = new PublicClientApplication(msalConfig);

msalInstance.addEventCallback((event) => {
    if (event.eventType === EventType.LOGIN_SUCCESS && event.payload.account) {
        const account = event.payload.account;
        msalInstance.setActiveAccount(account);
    }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <App instance={msalInstance}/>
);