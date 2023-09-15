import {JSEncrypt} from 'jsencrypt'

const StreamlitApp = ({token}) => {

    const encrypter = new JSEncrypt();
    encrypter.setPublicKey(`-----BEGIN PUBLIC KEY-----
    MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC8xCLFS8iIM7y304HbcPR/LH6b
    D0OBqVBeyRJLbjlN1dnYl+PhsZS/9Z22hkaF/W6cF7da/OawkG4CxVw+D0aGLReU
    ZzTRFu39Z6WaaVTWqPtHE2d/iXUAb5ZVDructHyEusLsps4XtxqmkHBP7t6EMeCN
    i2S2uZCQWatMpOwNjQIDAQAB
    -----END PUBLIC KEY-----`)
    const encryptedString = encrypter.encrypt(JSON.stringify({name: token.name, username: token.preferred_username}))

    return <>
    <iframe src={`http://localhost:8501/?data=${encodeURIComponent(encryptedString)}`} frameBorder="0" 
         style={{overflow:"hidden", display:"block", position: "absolute", height: "100%", width: "100%"}}></iframe>
    </>
};

export default StreamlitApp;