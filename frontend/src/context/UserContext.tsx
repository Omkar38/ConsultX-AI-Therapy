import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface UserContextType {
  username: string;
  setUsername: (username: string) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string>('');
  
  // Initialize username from localStorage on mount
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId) {
      setUsername(storedUserId);
    }
  }, []);
  
  // Update localStorage when username changes
  const handleSetUsername = (newUsername: string) => {
    setUsername(newUsername);
    localStorage.setItem('userId', newUsername);
  };
  
  return (
    <UserContext.Provider value={{ username, setUsername: handleSetUsername }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) throw new Error('useUser must be used within a UserProvider');
  return context;
}
