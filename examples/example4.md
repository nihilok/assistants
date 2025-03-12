>>> Give me those codeblocks with a `tsx` language tag instead of `typescript`.   

Here are the same codeblocks with the `tsx` language tag:

```tsx
// useCrypto.ts
import { useState, useCallback } from 'react';

/**
 * A hook that provides encryption and decryption functions using a provided CryptoKey
 * @param cryptoKey The CryptoKey to use for encryption/decryption operations
 */
export function useCrypto(cryptoKey: CryptoKey | null) {
  const [error, setError] = useState<Error | null>(null);

  /**
   * Encrypts any data structure into a string
   * @param data The data to encrypt (any type)
   * @returns Promise resolving to the encrypted string or null if error
   */
  const encrypt = useCallback(
    async <T>(data: T): Promise<string | null> => {
      if (!cryptoKey) {
        setError(new Error('No crypto key provided'));
        return null;
      }

      try {
        // Convert data to string
        const jsonString = JSON.stringify(data);
        const encodedData = new TextEncoder().encode(jsonString);
        
        // Generate random IV (Initialization Vector)
        const iv = crypto.getRandomValues(new Uint8Array(12)); // 12 bytes for AES-GCM
        
        // Encrypt the data
        const encryptedBuffer = await crypto.subtle.encrypt(
          {
            name: 'AES-GCM',
            iv
          },
          cryptoKey,
          encodedData
        );
        
        // Combine IV and encrypted data in a single buffer for storage
        const resultBuffer = new Uint8Array(iv.length + encryptedBuffer.byteLength);
        resultBuffer.set(iv, 0);
        resultBuffer.set(new Uint8Array(encryptedBuffer), iv.length);
        
        // Convert to Base64 string for storage/transmission
        return btoa(String.fromCharCode.apply(null, Array.from(resultBuffer)));
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        console.error('Encryption error:', error);
        return null;
      }
    },
    [cryptoKey]
  );

  /**
   * Decrypts an encrypted string back to its original data structure
   * @param encryptedString The encrypted string to decrypt
   * @returns Promise resolving to the original data structure or null if error
   */
  const decrypt = useCallback(
    async <T>(encryptedString: string): Promise<T | null> => {
      if (!cryptoKey) {
        setError(new Error('No crypto key provided'));
        return null;
      }

      try {
        // Convert Base64 string back to buffer
        const binaryString = atob(encryptedString);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Extract IV from the beginning of the data
        const iv = bytes.slice(0, 12);
        const encryptedData = bytes.slice(12);
        
        // Decrypt the data
        const decryptedBuffer = await crypto.subtle.decrypt(
          {
            name: 'AES-GCM',
            iv
          },
          cryptoKey,
          encryptedData
        );
        
        // Convert back to original data structure
        const decodedText = new TextDecoder().decode(decryptedBuffer);
        return JSON.parse(decodedText) as T;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        console.error('Decryption error:', error);
        return null;
      }
    },
    [cryptoKey]
  );

  return { encrypt, decrypt, error };
}
```

```tsx
// ExampleComponent.tsx
import React, { useState, useEffect } from 'react';
import { useCrypto } from './useCrypto';

// Example data interface
interface UserData {
  id: number;
  name: string;
  email: string;
  metadata?: Record<string, any>;
}

const ExampleComponent: React.FC = () => {
  const [cryptoKey, setCryptoKey] = useState<CryptoKey | null>(null);
  const [encryptedData, setEncryptedData] = useState<string | null>(null);
  const { encrypt, decrypt, error } = useCrypto(cryptoKey);

  // Generate a key when component mounts
  useEffect(() => {
    const generateKey = async () => {
      try {
        const key = await crypto.subtle.generateKey(
          {
            name: 'AES-GCM',
            length: 256
          },
          true, // extractable
          ['encrypt', 'decrypt']
        );
        setCryptoKey(key);
      } catch (err) {
        console.error('Error generating crypto key:', err);
      }
    };
    
    generateKey();
  }, []);

  const handleEncrypt = async () => {
    if (!cryptoKey) return;
    
    const userData: UserData = {
      id: 123,
      name: 'John Doe',
      email: 'john@example.com',
      metadata: {
        lastLogin: new Date().toISOString(),
        preferences: {
          theme: 'dark',
          notifications: true
        }
      }
    };
    
    const encrypted = await encrypt<UserData>(userData);
    setEncryptedData(encrypted);
    console.log('Encrypted data:', encrypted);
  };

  const handleDecrypt = async () => {
    if (!cryptoKey || !encryptedData) return;
    
    const decrypted = await decrypt<UserData>(encryptedData);
    console.log('Decrypted data:', decrypted);
  };

  return (
    <div>
      <h2>Crypto Example</h2>
      {error && <div style={{ color: 'red' }}>Error: {error.message}</div>}
      <div>
        <button onClick={handleEncrypt} disabled={!cryptoKey}>
          Encrypt Data
        </button>
        <button onClick={handleDecrypt} disabled={!cryptoKey || !encryptedData}>
          Decrypt Data
        </button>
      </div>
      {encryptedData && (
        <div style={{ marginTop: '20px' }}>
          <h3>Encrypted Result</h3>
          <div style={{ wordBreak: 'break-all' }}>{encryptedData}</div>
        </div>
      )}
    </div>
  );
};

export default ExampleComponent;
```