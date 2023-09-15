import { MsalProvider, AuthenticatedTemplate, useMsal, UnauthenticatedTemplate } from '@azure/msal-react';
import { loginRequest } from './authConfig';

import './styles/App.css';

import Landing from './components/Landing';
import StreamlitApp from './components/StreamlitApp';

const MainContent = () => {

    const { instance } = useMsal();
    const activeAccount = instance.getActiveAccount();

    const handleRedirect = () => {
        instance
            .loginRedirect({
                ...loginRequest,
                prompt: 'create',
            })
            .catch((error) => console.log(error));
    };
    return (
        <div className="App">
            <AuthenticatedTemplate>
                {activeAccount ? (
                      <StreamlitApp token={activeAccount.idTokenClaims} />
                ) : null}
            </AuthenticatedTemplate>
            <UnauthenticatedTemplate>
                <Landing redirectCallback={handleRedirect}/>
            </UnauthenticatedTemplate>
        </div>
    );
};


const App = ({ instance }) => {
    return (
        <MsalProvider instance={instance}>
            <MainContent />
        </MsalProvider>
    );
};

export default App;