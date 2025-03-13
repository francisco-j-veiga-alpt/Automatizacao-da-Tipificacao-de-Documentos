// /pages/UsersPage.tsx
import React, { useEffect, useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";

interface User {
  name: string;
  age: number;
  city: string;
}

interface ApiResponse {
  list: User[];
}

const UsersPage: React.FC = () => {
  const [data, setData] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const number = searchParams.get("number");
  const apiUrl =
    "http://localhost:8000/list-users" + (number ? `?number=${number}` : "");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const result: ApiResponse = await response.json();
        setData(result.list);
      } catch (error) {
        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError("An unknown error occurred");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [apiUrl]);

  const goToDeleteUserPage = () => {
    navigate("/delete-user");
  };

  const goToEditUserPage = (user: User) => {
    navigate(`/update-user`);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Users</h1>
      <Link to="/add-user">Add User</Link>
      <button onClick={goToDeleteUserPage}>Delete User</button>
      {data.length === 0 ? (
        <div>No users found.</div>
      ) : (
        <ul>
          {data.map((item, index) => (
            <li key={index}>
              {item.name}
              <br />
              Age: {item.age}
              <br />
              City: {item.city}
              <button onClick={() => goToEditUserPage(item)}>Edit</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default UsersPage;
