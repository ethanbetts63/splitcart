import { Button } from "@/components/ui/button"
import { Link, useNavigate } from "react-router-dom"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { useAuth } from "@/context/AuthContext"

export function SignupForm({ ...props }: React.ComponentProps<typeof Card>) {
  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrors({})

    if (password !== confirmPassword) {
      setErrors({ password2: ["Passwords do not match!"] })
      return
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/registration/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            full_name: fullName,
            email,
            password1: password,
            password2: confirmPassword,
          }),
        }
      )

      if (response.ok) {
        const data = await response.json()
        console.log("Registration successful", data)
        login(data.key)
        navigate("/")
      } else {
        const errorData = await response.json()
        setErrors(errorData)
        console.error("Registration failed:", errorData)
      }
    } catch (error) {
      console.error("An error occurred during registration:", error)
      setErrors({ non_field_errors: ["An unexpected error occurred."] })
    }
  }

  return (
    <Card {...props}>
      <CardHeader>
        <CardTitle>Create an account</CardTitle>
        <CardDescription>
          Enter your information below to create your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <FieldGroup>
            {errors.non_field_errors && (
              <div className="rounded-md border border-red-500 bg-red-50 p-4 text-sm text-red-700">
                {errors.non_field_errors.map((error, index) => (
                  <p key={index}>{error}</p>
                ))}
              </div>
            )}
            <Field>
              <FieldLabel htmlFor="name">Full Name</FieldLabel>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
              {errors.full_name && (
                <FieldDescription className="text-red-500">
                  {errors.full_name[0]}
                </FieldDescription>
              )}
            </Field>
            <Field>
              <FieldLabel htmlFor="email">Email</FieldLabel>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              {errors.email ? (
                <FieldDescription className="text-red-500">
                  {errors.email[0]}
                </FieldDescription>
              ) : (
                <FieldDescription>
                  We&apos;ll use this to contact you. We will not share your
                  email with anyone else.
                </FieldDescription>
              )}
            </Field>
            <Field>
              <FieldLabel htmlFor="password">Password</FieldLabel>
              <Input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              {errors.password1 ? (
                <FieldDescription className="text-red-500">
                  {errors.password1.join(" ")}
                </FieldDescription>
              ) : (
                <FieldDescription>
                  Must be at least 8 characters long.
                </FieldDescription>
              )}
            </Field>
            <Field>
              <FieldLabel htmlFor="confirm-password">
                Confirm Password
              </FieldLabel>
              <Input
                id="confirm-password"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
              {errors.password2 && (
                <FieldDescription className="text-red-500">
                  {errors.password2.join(" ")}
                </FieldDescription>
              )}
            </Field>
            <FieldGroup>
              <Field>
                <Button type="submit">Create Account</Button>
                <FieldDescription className="px-6 text-center">
                  Already have an account?{" "}
                  <Link to="/login" className="underline">
                    Sign in
                  </Link>
                </FieldDescription>
              </Field>
            </FieldGroup>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  )
}